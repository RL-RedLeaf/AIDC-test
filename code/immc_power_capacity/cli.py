import argparse
import importlib
import json
import sys
from pathlib import Path

import yaml

from .calculator import combined_battery, grid_only, hydro, solar, thermal, wind
from .exceptions import CapacityModelError, ValidationError
from .validators import _k_factor, _positive


WRONG_UNIT_KEYS = {
    "P_grid_mva": "P_grid 必须用换算后的 P_grid_mw（MW）；MVA 需先乘功率因数并注明口径。",
    "C_max_mwh": "充电功率必须用 C_max_mw（MW）；MWh 是能量。",
    "D_max_mwh": "放电功率必须用 D_max_mw（MW）；MWh 是能量。",
    "E_usable_mw": "可用电量必须用 E_usable_mwh（MWh）；MW 是功率。",
    "supply_series_mwh": "逐时功率序列必须用 supply_series_mw（MW）；不能把 MWh 当 MW。",
    "net_output_mwh": "逐时净出力必须用 net_output_mw（MW）；不能把 MWh 当 MW。",
    "power_ratios_mwh": "归一化出力应使用 power_ratios，单位为 MWh/MWh，无量纲。",
}


def build_parser():
    parser = argparse.ArgumentParser(
        description="IMMC 2027 A 题第一问：计算候选供电方案的最大额定 IT 容量。"
    )
    parser.add_argument("config", help="YAML 配置路径。")
    parser.add_argument("--json", default=None, help="同时写出 JSON 结果文件。")
    return parser


def run(config_path, json_path=None):
    path = Path(config_path)
    if not path.exists():
        raise CapacityModelError(f"配置文件不存在：{path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise CapacityModelError(f"YAML 解析失败：{exc}") from exc
    if not isinstance(data, dict):
        raise CapacityModelError("YAML 顶层必须是对象。")

    _reject_wrong_units(data)
    grid_value = _number(data, "P_grid_mw")
    k_value = _number(data, "k_factor")
    try:
        _positive("P_grid_mw", grid_value)
        _k_factor(k_value)
    except ValidationError as exc:
        raise CapacityModelError(str(exc)) from exc
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise CapacityModelError("配置中的 scenarios 至少要包含一套方案。")

    results = []
    for index, spec in enumerate(scenarios, start=1):
        if not isinstance(spec, dict) or "type" not in spec:
            raise CapacityModelError(f"第 {index} 个方案缺少 type 字段。")
        kind = str(spec["type"]).strip().lower()
        name = str(spec.get("name", f"方案 {index}")).strip()
        if not name:
            raise CapacityModelError(f"第 {index} 个方案的 name 不能为空。")
        _reject_wrong_units(spec, name)
        if isinstance(spec.get("battery"), dict):
            _reject_wrong_units(spec["battery"], f"{name}.battery")
        scenario_k = (
            _number(spec, "k_factor")
            if spec.get("k_factor") is not None
            else k_value
        )
        result = _build_scenario(kind, spec, grid_value, scenario_k, name)
        result["name"] = name
        results.append(result)

    optimal = max(results, key=lambda item: item["breakdown"]["it_mw"])
    report = {
        "assumptions": {
            "P_grid_mw": grid_value,
            "k_factor": k_value,
            "k_source": data.get("k_source", "未注明"),
            "period_note": data.get("period_note", "结果仅解释配置中给出的考察期"),
        },
        "scenarios": results,
        "optimum": optimal,
    }
    if json_path:
        output = Path(json_path)
        try:
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            raise CapacityModelError(f"无法写入 JSON 结果：{exc}") from exc
    return report


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = run(args.config, args.json)
    except CapacityModelError as exc:
        print(f"[输入或模型错误] {exc}", file=sys.stderr)
        return 2
    _print(report)
    return 0


def _build_scenario(kind, spec, grid_value, k_value, name):
    if kind == "grid":
        return grid_only(grid_value, k_value)
    if kind == "coal":
        return thermal(
            "coal", grid_value, k_value,
            _number(spec, "units"), _number(spec, "unit_net_mw"),
            _optional(spec, "net_efficiency"),
        )
    if kind == "gas":
        return thermal(
            "gas", grid_value, k_value,
            _number(spec, "units"), _number(spec, "unit_net_mw"),
            _optional(spec, "net_efficiency"), spec.get("gas_supply_adequate"),
        )
    if kind == "wind":
        return _wind_result(spec, grid_value, k_value)
    if kind == "hydro":
        return hydro(
            name, grid_value, k_value,
            _number(spec, "installed_mw"), _number(spec, "flow_m3_per_s"),
            _number(spec, "net_head_m"), _number(spec, "efficiency"),
        )
    if kind == "solar":
        return _solar_result(spec, grid_value, k_value)
    if kind == "combined_battery":
        return combined_battery(
            name, grid_value, k_value,
            _series(spec, "supply_series_mw", required=True),
            _number(spec, "installed_mw"), _number(spec, "dt_hours"),
            spec.get("battery"),
        )
    raise CapacityModelError(
        f"不支持的方案类型：{kind}。可选值：grid, coal, gas, wind, hydro, solar, combined_battery。"
    )


def _wind_result(spec, grid_value, k_value):
    provided = [
        field for field in ("alpha", "power_ratios", "net_output_mw")
        if spec.get(field) is not None
    ]
    if len(provided) != 1:
        raise CapacityModelError("风电方案必须在 alpha、power_ratios、net_output_mw 中提供且只提供一个。")
    source = provided[0]
    series = _series(spec, source, required=False) if source != "alpha" else None
    return wind(
        "wind", grid_value, k_value,
        area_km2=spec.get("area_km2"),
        density_mw_per_km2=spec.get("density_mw_per_km2"),
        installed_mw=spec.get("installed_mw"),
        alpha=spec.get("alpha"),
        power_ratios=series if source == "power_ratios" else None,
        net_output_mw=series if source == "net_output_mw" else None,
    )


def _solar_result(spec, grid_value, k_value):
    provided = [
        field for field in ("supply_ratios", "net_output_mw")
        if spec.get(field) is not None
    ]
    if len(provided) != 1:
        raise CapacityModelError("光伏方案必须在 supply_ratios 与 net_output_mw 中提供且只提供一个。")
    source = provided[0]
    return solar(
        "solar", grid_value, k_value,
        _number(spec, "area_km2"), _number(spec, "density_mw_per_km2"),
        supply_ratios=_series(spec, source, required=True) if source == "supply_ratios" else None,
        net_output_mw=_series(spec, source, required=True) if source == "net_output_mw" else None,
        dt_hours=_number(spec, "dt_hours"),
        battery=spec.get("battery"),
    )


def _series(spec, field, required):
    if field not in spec or spec[field] is None:
        if required:
            raise CapacityModelError(f"{field} 不能缺失。")
        return None
    path = spec[field]
    if not isinstance(path, str):
        return path
    if "::" not in path:
        raise CapacityModelError(
            f"{field} 若是外部序列，请写成 'module::variable'；否则请直接给 YAML/JSON 数组。"
        )
    module_name, attr = path.split("::", 1)
    try:
        module = importlib.import_module(module_name)
        return getattr(module, attr)
    except (ImportError, AttributeError) as exc:
        raise CapacityModelError(f"无法加载 {field} 的外部序列 {path}：{exc}") from exc


def _number(spec, field):
    if field not in spec or spec[field] is None:
        raise CapacityModelError(f"{field} 不能缺失。")
    value = spec[field]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise CapacityModelError(f"{field} 必须是数值。")
    return value


def _optional(spec, field):
    return None if field not in spec or spec[field] is None else _number(spec, field)


def _reject_wrong_units(mapping, label="配置"):
    if not isinstance(mapping, dict):
        return
    for key, message in WRONG_UNIT_KEYS.items():
        if key in mapping:
            raise CapacityModelError(f"{label}.{key} 单位错误：{message}")


def _print(report):
    print("电网 MW | 方案 | 自发电可靠 MW | 设施总 MW | k | 最大 IT MW")
    for item in report["scenarios"]:
        row = item["breakdown"]
        print(
            f"{row['grid_mw']:.6g} | {item['name']} | "
            f"{row['self_generation_mw']:.6g} | {row['facility_mw']:.6g} | "
            f"{row['k']:.6g} | {row['it_mw']:.6g}"
        )
    optimum = report["optimum"]
    print(
        f"\n最优方案：{optimum['name']}，"
        f"P_E={optimum['breakdown']['it_mw']:.6g} MW IT"
    )
    print(f"考察期说明：{report['assumptions']['period_note']}")


if __name__ == "__main__":
    raise SystemExit(main())
