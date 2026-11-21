"""命令行、配置读写和控制台输入向导。"""

import argparse
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path

import yaml

from .core import (
    CapacityModelError,
    ValidationError,
    _build_scenario,
    _config_number,
    _k_factor,
    _positive,
    assess_site,
)


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
        description="IMMC 2027 A 题第一问：计算场址电、水、土地联合容量。"
    )
    parser.add_argument("config", nargs="?", help="YAML 配置路径；省略时进入中文输入向导。")
    parser.add_argument("--json", default=None, help="同时写出 JSON 结果文件。")
    parser.add_argument("--interactive", action="store_true", help="强制进入中文输入向导。")
    return parser


def calculate(config, json_path=None):
    """直接接收配置字典或 YAML 路径，供 Python 脚本调用。"""
    if isinstance(config, Mapping):
        data = dict(config)
    else:
        data = _load_config(config)

    if data.get("model") == "q1":
        report = assess_site(data)
    else:
        if "model" in data or any(key in data for key in ("water", "land", "assessment_year")):
            raise CapacityModelError("正稿联合评估配置需声明 model: q1。")
        report = _power_report(data)
    if json_path:
        output = Path(json_path)
        try:
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        except OSError as exc:
            raise CapacityModelError(f"无法写入 JSON 结果：{exc}") from exc
    return report


def run(config_path, json_path=None):
    """兼容原命令行调用，等价于 calculate(config_path, json_path)."""
    return calculate(config_path, json_path)


def _load_config(config_path):
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
    return data


def _power_report(data):
    _reject_wrong_units(data)
    grid_value = _config_number(data, "P_grid_mw")
    k_value = _config_number(data, "k_factor")
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
            _config_number(spec, "k_factor")
            if spec.get("k_factor") is not None
            else k_value
        )
        result = _build_scenario(kind, spec, grid_value, scenario_k, name)
        result["name"] = name
        results.append(result)

    optimal = max(results, key=lambda item: item["breakdown"]["it_mw"])
    return {
        "assumptions": {
            "P_grid_mw": grid_value,
            "k_factor": k_value,
            "k_source": data.get("k_source", "未注明"),
            "period_note": data.get("period_note", "结果仅解释配置中给出的考察期"),
        },
        "scenarios": results,
        "optimum": optimal,
    }


def _reject_wrong_units(mapping, label="配置"):
    if not isinstance(mapping, dict):
        return
    for key, message in WRONG_UNIT_KEYS.items():
        if key in mapping:
            raise CapacityModelError(f"{label}.{key} 单位错误：{message}")


def _print(report, say=print):
    if "P_max_mw_it" in report:
        say("评估设置")
        say(f"  场址：{report['site']}")
        say(f"  评估年份 y：{report['assessment_year']}")
        say(f"  设计期：{report['period_note']}")
        say(f"  服务水平：{report['service_level']}")
        water = report["water"]
        basis = "取水上界" if water["basis"] == "withdrawal" else "耗水上限"
        say("")
        say("水量约束")
        say(f"  口径：{basis}")
        say(f"  Q_max = {water['Q_max_m3_h']:.6g} m³/h")
        say(f"  未纳入的水量项：{', '.join(water['omitted']) or '无'}")
        say("")
        say("候选方案")
        for index, row in enumerate(report["scenarios"], start=1):
            power = row["breakdown"]
            say(f"[{index}] {row['name']}（{row['power_type']}）")
            say(f"  电力上限 P_E = {row['P_E_mw_it']:.6g} MW IT")
            say(f"    P_grid = {power['grid_mw']:.6g} MW，P_self = {power['self_generation_mw']:.6g} MW，"
                f"P_total = {power['facility_mw']:.6g} MW，k = {power['k']:.6g}")
            if row["P_W_mw_it"] is None:
                say("  水上限 P_W = 无现场用水需求")
            else:
                say(f"  水上限 P_W = {row['P_W_mw_it']:.6g} MW IT（Q_max / WUE）")
            say(f"  土地上限 P_L = {row['P_L_mw_it']:.6g} MW IT")
            say(f"  联合容量 P = {row['P_mw_it']:.6g} MW IT；触顶约束：{'、'.join(row['binding'])}")
            say("")
        for item in report["excluded"]:
            say(f"未进入比较：{item['name']}（{item['reason']}，投运年 {item['online_year']}）")
        say("结论")
        say(f"  P_max = {report['P_max_mw_it']:.6g} MW IT")
        say(f"  最优配置：{'、'.join(report['winners'])}")
        return
    say("电力分项结果")
    for item in report["scenarios"]:
        row = item["breakdown"]
        say(
            f"{item['name']}：P_grid = {row['grid_mw']:.6g} MW，"
            f"P_self = {row['self_generation_mw']:.6g} MW，"
            f"P_total = {row['facility_mw']:.6g} MW，"
            f"k = {row['k']:.6g}，P_E = {row['it_mw']:.6g} MW IT"
        )
    optimum = report["optimum"]
    say(
        f"\n最优方案：{optimum['name']}，P_E = {optimum['breakdown']['it_mw']:.6g} MW IT"
    )
    say(f"考察期说明：{report['assumptions']['period_note']}")


def _ask_text(asker, prompt, default=None, allow_blank=False):
    suffix = f" [{default}]" if default is not None else ""
    raw = asker(f"{prompt}{suffix}：").strip()
    if not raw:
        if default is not None:
            return default
        if allow_blank:
            return None
        raise CapacityModelError(f"{prompt}不能为空。")
    return raw


def _ask_number(asker, prompt, default=None, minimum=None, maximum=None,
                allow_zero=True, integer=False):
    while True:
        raw = _ask_text(asker, prompt, default)
        try:
            value = int(raw) if integer else float(raw)
        except ValueError:
            print("请输入有效数字。")
            continue
        if not allow_zero and value == 0:
            print("该值必须大于零。")
            continue
        if minimum is not None and value < minimum:
            print(f"该值不能小于 {minimum:g}。")
            continue
        if maximum is not None and value > maximum:
            print(f"该值不能大于 {maximum:g}。")
            continue
        return value


def _ask_optional_number(asker, prompt):
    while True:
        raw = _ask_text(asker, prompt, allow_blank=True)
        if raw is None:
            return None
        try:
            return float(raw)
        except ValueError:
            print("请输入数字或直接回车留空。")


def _ask_choice(asker, prompt, options, default):
    labels = "，".join(f"{index}={value}" for index, value in enumerate(options, start=1))
    while True:
        raw = _ask_text(asker, f"{prompt}（{labels}）", str(default))
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        if raw in options:
            return raw
        print("请输入选项编号。")


def _ask_yes_no(asker, prompt, default=True):
    return _ask_choice(asker, prompt, ["是", "否"], "是" if default else "否") == "是"


def _ask_series(asker, prompt):
    while True:
        raw = _ask_text(asker, prompt)
        parts = [part for part in re.split(r"[,，\s]+", raw.strip()) if part]
        try:
            values = [float(part) for part in parts]
        except ValueError:
            print("请输入逗号或空格分隔的数值序列。")
            continue
        if values:
            return values
        print("序列不能为空。")


def _ask_battery(asker, default=True):
    if not _ask_yes_no(asker, "是否配置电池（有电池时按式(6)校核充放电与夜间供电）", default):
        return None
    return {
        "C_max_mw": _ask_number(asker, "最大充电功率 C_max_mw（C_max，MW）", 10, allow_zero=False),
        "D_max_mw": _ask_number(asker, "最大放电功率 D_max_mw（D_max，MW）", 10, allow_zero=False),
        "E_usable_mwh": _ask_number(asker, "可用电量 E_usable_mwh（E_usable，MWh）", 10, allow_zero=False),
        "charge_efficiency": _ask_number(
            asker, "充电效率（η_c）", 1, minimum=0.000001, maximum=1, allow_zero=False
        ),
        "discharge_efficiency": _ask_number(
            asker, "放电效率（η_d）", 1, minimum=0.000001, maximum=1, allow_zero=False
        ),
    }


def _ask_site(asker):
    return {
        "site": _ask_text(asker, "场址名称（本次评估的同一场址）", "演示场址"),
        "assessment_year": _ask_number(asker, "评估年份 y（只比较该年之前已投运的配置）", 2028,
                                       minimum=1, integer=True, allow_zero=False),
        "period_note": _ask_text(asker, "设计期说明（电力、水和土地必须使用同一设计期）", "枯水期设计工况"),
        "service_level": _ask_text(asker, "服务水平（本次容量对应的正常运营条件）", "正常运营，持续满载"),
    }


def _ask_power_inputs(asker):
    mode = _ask_choice(asker, "电网输入方式（P_grid 为接入点可持续交付净有功；MVA 仅作初筛换算）",
                       ["MW", "MVA"], "MW")
    config = {}
    if mode == "MVA":
        config["P_grid_mva"] = _ask_number(asker, "电网视在功率 S_grid（P_grid_mva，MVA）", 120,
                                           minimum=0, allow_zero=False)
        config["power_factor"] = _ask_number(
            asker, "功率因数 cos φ（仅用于 P_grid=S_grid·cos φ）", 0.9,
            minimum=0.000001, maximum=1, allow_zero=False
        )
    else:
        config["P_grid_mw"] = _ask_number(asker, "电网可持续有功 P_grid（P_grid_mw，MW）", 108, minimum=0)
    config["k_factor"] = _ask_number(
        asker, "满载设施/IT 倍率 k（设计满载设施功率÷同一工况 IT 功率）", 1.2,
        minimum=1, allow_zero=False
    )
    return config


def _ask_water(asker):
    basis = _ask_choice(asker, "水量口径（耗水或取水；Q_max 与 WUE 必须同口径）",
                         ["consumption", "withdrawal"], "consumption")
    wue = _ask_number(asker, "WUE（每 kWh IT 的取水/耗水量，L/kWh IT；P_W=Q_max/WUE）", 1.5, minimum=0)
    limits = {}
    while not limits:
        print("请至少提供 Q_source、Q_stress、Q_policy 中的一项，作为式(8)的独立水量上限，单位 m³/h。")
        for key, label in (
            ("source", "水源可用上限 Q_source（source_m3_h；扣除生态保留和既有取水）"),
            ("stress", "水压力允许上限 Q_stress（stress_m3_h；按本地水压力阈值）"),
            ("policy", "许可或合同上限 Q_policy（policy_m3_h；政策允许的取水上限）"),
        ):
            value = _ask_optional_number(asker, f"{label}（可留空）")
            if value is not None:
                limits[key] = value
    return {
        "basis": basis,
        "wue_l_per_kwh_it": wue,
        **{f"{key}_m3_h": value for key, value in limits.items()},
    }


def _ask_land(asker):
    return {
        "effective_ha": _ask_number(asker, "场址总有效用地 A_eff（effective_ha，ha）", 160,
                                    minimum=0, allow_zero=False),
        "fixed_it_ha": _ask_number(asker, "IT 侧固定用地 A_0^IT（fixed_it_ha，ha；0 表示乐观上界）", 10,
                                   minimum=0),
        "ha_per_mw_it": _ask_number(asker, "园区边际用地强度 a_site（ha/MW IT）", 1,
                                    minimum=0.000001, allow_zero=False),
    }


def _ask_scenario(asker, number, grid_mw):
    kind = _ask_choice(
        asker,
        "方案类型（每个方案对应式(1)中的一个候选配置 x）",
        ["grid", "coal", "gas", "wind", "hydro", "solar", "combined_battery"],
        "grid",
    )
    spec = {
        "name": _ask_text(asker, "方案名称（唯一标识配置 x）", f"{kind}-{number}"),
        "type": kind,
        "online_year": _ask_number(asker, "投运年份（是否属于评估年份 y 的可行集合 X_y）", 2028,
                                   minimum=1, integer=True, allow_zero=False),
    }
    wue = _ask_optional_number(asker, "本方案 WUE(x) 覆盖（L/kWh IT，可留空）")
    if wue is not None:
        spec["wue_l_per_kwh_it"] = wue

    if kind in {"coal", "gas"}:
        spec["units"] = _ask_number(asker, "可同时运行机组台数 N_j", 2 if kind == "coal" else 1,
                                    minimum=1, integer=True, allow_zero=False)
        spec["unit_net_mw"] = _ask_number(asker, "单机持续净功率 p_j^net（MW，已扣厂用电）",
                                          80 if kind == "coal" else 60,
                                          minimum=0.000001, allow_zero=False)
        efficiency = _ask_optional_number(asker, "净效率（仅报告燃料热功率，不改变 P_j；可留空）")
        if efficiency is not None:
            spec["net_efficiency"] = efficiency
        if kind == "gas":
            spec["gas_supply_adequate"] = _ask_yes_no(asker, "供气是否充足（燃气容量上界的前提）", True)
    elif kind == "wind":
        installed = _ask_optional_number(asker, "风电装机 X_wind（MW；留空则用 A_wind×ρ_wind）")
        if installed is None:
            spec["area_km2"] = _ask_number(asker, "风电合格面积 A_wind（km²）", 10,
                                           minimum=0.000001, allow_zero=False)
            spec["density_mw_per_km2"] = _ask_number(asker, "风电装机密度 ρ_wind（MW/km²）", 8,
                                                     minimum=0.000001, allow_zero=False)
        else:
            spec["installed_mw"] = installed
        if grid_mw > 0:
            spec["net_output_mw"] = _ask_series(asker, "同期风电逐时净功率 r_t（net_output_mw，MW）")
        elif _ask_yes_no(asker, "是否输入同期风电逐时净功率 r_t", True):
            spec["net_output_mw"] = _ask_series(asker, "同期风电逐时净功率 r_t（net_output_mw，MW）")
        else:
            spec["alpha"] = _ask_number(asker, "考察期最低净出力/装机 α_wind（孤立恒载口径）", 0.2,
                                        minimum=0, maximum=1)
    elif kind == "hydro":
        spec["installed_mw"] = _ask_number(asker, "水电装机 X_hydro（MW）", 80,
                                           minimum=0.000001, allow_zero=False)
        spec["flow_m3_per_s"] = _ask_number(asker, "可用流量 Q（m³/s，同一约束期）", 100,
                                            minimum=0.000001, allow_zero=False)
        spec["net_head_m"] = _ask_number(asker, "净落差 H（m，同一约束期）", 100,
                                         minimum=0.000001, allow_zero=False)
        spec["efficiency"] = _ask_number(asker, "综合效率 η_hydro（0–1）", 0.9,
                                         minimum=0.000001, maximum=1, allow_zero=False)
    elif kind == "solar":
        spec["area_km2"] = _ask_number(asker, "光伏合格面积 A_PV（km²）", 5,
                                       minimum=0.000001, allow_zero=False)
        spec["density_mw_per_km2"] = _ask_number(asker, "光伏装机密度 ρ_PV（MW/km²）", 100,
                                                 minimum=0.000001, allow_zero=False)
        spec["dt_hours"] = _ask_number(asker, "时段长度 Δt（dt_hours，h；只用于内部逐时校核）", 1,
                                       minimum=0.000001, allow_zero=False)
        spec["net_output_mw"] = _ask_series(asker, "光伏逐时净功率 r_t（net_output_mw，MW）")
        battery = _ask_battery(asker, True)
        if battery is not None:
            spec["battery"] = battery
    elif kind == "combined_battery":
        spec["installed_mw"] = _ask_number(
            asker, "风光合计装机 X_wind + X_PV（MW）", 230, minimum=0.000001, allow_zero=False
        )
        spec["dt_hours"] = _ask_number(
            asker, "时段长度 Δt（dt_hours，h；只用于附录 A 的逐时校核）", 1,
            minimum=0.000001, allow_zero=False
        )
        spec["supply_series_mw"] = _ask_series(
            asker, "风光同期合计净功率 r_t（supply_series_mw，MW）"
        )
        spec["battery"] = _ask_battery(asker, True)
    return spec


def build_interactive_config(asker=input, say=print, default_json=None):
    """收集一套 Q1 配置，供函数调用和测试复用。"""
    say("IMMC 2027 A 题第一问：交互式电水土地容量计算")
    say("说明：本向导按正文式(1)-(16)收集同一场址、同一设计期和同一服务水平下的候选配置 x。")
    data = _ask_site(asker)
    data["model"] = "q1"
    data.update(_ask_power_inputs(asker))
    grid_mw = data.get("P_grid_mw", data.get("P_grid_mva", 0) * data.get("power_factor", 1))
    data["water"] = _ask_water(asker)
    data["land"] = _ask_land(asker)
    data["scenarios"] = []
    while True:
        index = len(data["scenarios"]) + 1
        data["scenarios"].append(_ask_scenario(asker, index, grid_mw))
        if not _ask_yes_no(asker, "继续添加方案（每个方案是式(1)中的一个候选配置 x）", False):
            break
    if default_json:
        output_path = str(default_json)
        say(f"JSON 输出：{output_path}")
    else:
        output_path = _ask_text(asker, "JSON 输出路径（保存计算结果；留空只在终端显示）", allow_blank=True)
    return data, output_path


def run_interactive(asker=input, say=print, default_json=None):
    """运行输入向导，返回进程退出码。"""
    try:
        config, output_path = build_interactive_config(asker, say, default_json)
        report = calculate(config, output_path)
    except (EOFError, KeyboardInterrupt):
        say("已取消输入。")
        return 130
    except CapacityModelError as exc:
        say(f"[输入或模型错误] {exc}")
        return 2
    _print(report, say=say)
    return 0


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    args = build_parser().parse_args(argv)
    try:
        if args.interactive or args.config is None:
            return run_interactive(default_json=args.json)
        report = calculate(args.config, args.json)
    except CapacityModelError as exc:
        print(f"[输入或模型错误] {exc}", file=sys.stderr)
        return 2
    _print(report)
    return 0
