import argparse
import json
import sys
from pathlib import Path

import yaml

from .supply import _build_scenario, _number
from .site import assess_site, sensitivity_cases
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
        description="IMMC 2027 A 题第一问：计算场址联合容量或电力分项容量。"
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

    if data.get("model") == "q1":
        report = assess_site(data)
        report["sensitivity"] = sensitivity_cases(data)
    else:
        if "model" in data or any(key in data for key in ("water", "land", "C_PCC_mw", "assessment_year")):
            raise CapacityModelError("正稿联合评估配置需声明 model: q1。")
        report = _power_report(data)
    if json_path:
        output = Path(json_path)
        try:
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        except OSError as exc:
            raise CapacityModelError(f"无法写入 JSON 结果：{exc}") from exc
    return report


def _power_report(data):
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




def _reject_wrong_units(mapping, label="配置"):
    if not isinstance(mapping, dict):
        return
    for key, message in WRONG_UNIT_KEYS.items():
        if key in mapping:
            raise CapacityModelError(f"{label}.{key} 单位错误：{message}")


def _print(report):
    if "P_max_mw_it" in report:
        print(f"{report['site']} | {report['assessment_year']} | {report['period_note']} | {report['service_level']}")
        water = report["water"]
        basis = "取水上界" if water["basis"] == "withdrawal" else "耗水上限"
        print(f"{basis} {water['Q_max_m3_h']:.6g} m³/h；未纳入水量项：{', '.join(water['omitted']) or '无'}")
        print("配置 | 电网 MW | 自建 MW | 进线 MW | k | P_E | P_W | P_L | 联合容量 (MW IT) | 触顶约束")
        for row in report["scenarios"]:
            power = row["breakdown"]
            water_text = "无现场用水需求" if row["P_W_mw_it"] is None else f"{row['P_W_mw_it']:.6g}"
            print(f"{row['name']} | {power['grid_mw']:g} | {power['self_generation_mw']:g} | "
                  f"{power['facility_mw']:g} | {power['k']:g} | {row['P_E_mw_it']:.6g} | "
                  f"{water_text} | {row['P_L_mw_it']:.6g} | {row['P_mw_it']:.6g} | {'、'.join(row['binding'])}")
        for item in report["excluded"]:
            print(f"排除：{item['name']}（{item['reason']}，投运年 {item['online_year']}）")
        print(f"P_max = {report['P_max_mw_it']:.6g} MW IT，最优配置：{'、'.join(report['winners'])}")
        return
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
