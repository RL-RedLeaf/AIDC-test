"""面向控制台的中文输入向导。"""

import re

from .exceptions import CapacityModelError


def _text(asker, prompt, default=None, allow_blank=False):
    suffix = f" [{default}]" if default is not None else ""
    raw = asker(f"{prompt}{suffix}：").strip()
    if not raw:
        if default is not None:
            return default
        if allow_blank:
            return None
        raise CapacityModelError(f"{prompt}不能为空。")
    return raw


def _number(asker, prompt, default=None, minimum=None, maximum=None,
            allow_zero=True, integer=False):
    while True:
        raw = _text(asker, prompt, default)
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


def _optional_number(asker, prompt, integer=False):
    while True:
        raw = _text(asker, prompt, allow_blank=True)
        if raw is None:
            return None
        try:
            return int(raw) if integer else float(raw)
        except ValueError:
            print("请输入数字或直接回车留空。")


def _choice(asker, prompt, options, default):
    labels = "，".join(f"{index}={value}" for index, value in enumerate(options, start=1))
    while True:
        raw = _text(asker, f"{prompt}（{labels}）", str(default))
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        if raw in options:
            return raw
        print("请输入选项编号。")


def _yes_no(asker, prompt, default=True):
    value = _choice(asker, prompt, ["是", "否"], "是" if default else "否")
    return value == "是"


def _series(asker, prompt):
    while True:
        raw = _text(asker, prompt)
        parts = [part for part in re.split(r"[,，\s]+", raw.strip()) if part]
        try:
            values = [float(part) for part in parts]
        except ValueError:
            print("请输入逗号或空格分隔的数值序列。")
            continue
        if not values:
            print("序列不能为空。")
            continue
        return values


def _ask_battery(asker, default=True, required=False):
    if not required and not _yes_no(asker, "是否配置电池", default):
        return None
    return {
        "C_max_mw": _number(asker, "最大充电功率 C_max_mw", 10, allow_zero=False),
        "D_max_mw": _number(asker, "最大放电功率 D_max_mw", 10, allow_zero=False),
        "E_usable_mwh": _number(asker, "可用电量 E_usable_mwh", 10, allow_zero=False),
        "charge_efficiency": _number(
            asker, "充电效率", 1, minimum=0.000001, maximum=1, allow_zero=False
        ),
        "discharge_efficiency": _number(
            asker, "放电效率", 1, minimum=0.000001, maximum=1, allow_zero=False
        ),
    }


def _ask_site(asker):
    return {
        "site": _text(asker, "场址名称", "演示场址"),
        "assessment_year": _number(asker, "评估年份", 2028, minimum=1, integer=True, allow_zero=False),
        "period_note": _text(asker, "设计期说明", "枯水期设计工况"),
        "service_level": _text(asker, "服务水平", "正常运营，持续满载"),
    }


def _ask_power_inputs(asker, joint):
    mode = _choice(asker, "电网输入方式", ["MW", "MVA"], "MW")
    config = {}
    if mode == "MVA":
        config["P_grid_mva"] = _number(asker, "电网视在功率 P_grid_mva", 120, minimum=0, allow_zero=False)
        config["power_factor"] = _number(
            asker, "功率因数", 0.9, minimum=0.000001, maximum=1, allow_zero=False
        )
    else:
        config["P_grid_mw"] = _number(asker, "电网可持续有功 P_grid_mw", 108, minimum=0, allow_zero=not joint)
    pcc = _optional_number(asker, "共享关口容量 C_PCC_mw（留空表示专用接线）")
    if pcc is not None:
        config["C_PCC_mw"] = pcc
    config["k_factor"] = _number(asker, "满载设施/IT 倍率 k", 1.2, minimum=1, allow_zero=False)
    return config


def _ask_water(asker):
    basis = _choice(asker, "水量口径", ["consumption", "withdrawal"], "consumption")
    wue = _number(asker, "WUE（L/kWh IT）", 1.5, minimum=0)
    limits = {}
    while not limits:
        print("请至少填写 source、stress、policy 中的一项水量上限，单位 m³/h。")
        for key, label in (
            ("source", "水源可用上限 source_m3_h"),
            ("stress", "水压力允许上限 stress_m3_h"),
            ("policy", "许可或合同上限 policy_m3_h"),
        ):
            value = _optional_number(asker, f"{label}（可留空）")
            if value is not None:
                limits[key] = value
    return {
        "basis": basis,
        "wue_l_per_kwh_it": wue,
        **{f"{key}_m3_h": value for key, value in limits.items()},
    }


def _ask_land(asker):
    return {
        "effective_ha": _number(asker, "场址有效用地 ha", 160, minimum=0, allow_zero=False),
        "fixed_it_ha": _number(asker, "IT 侧固定用地 ha", 10, minimum=0),
        "ha_per_mw_it": _number(asker, "园区边际用地强度 ha/MW IT", 1, minimum=0.000001, allow_zero=False),
        "generation_share": _number(asker, "本地发电及配套用地份额", 0, minimum=0, maximum=1),
    }


def _ask_scenario(asker, number, joint, grid_mw):
    kind = _choice(
        asker,
        "方案类型",
        ["grid", "coal", "gas", "wind", "hydro", "solar", "combined_battery"],
        "grid",
    )
    spec = {
        "name": _text(asker, "方案名称", f"{kind}-{number}"),
        "type": kind,
    }
    if joint:
        spec["online_year"] = _number(asker, "投运年份", 2028, minimum=1, integer=True, allow_zero=False)
        generation_share = _optional_number(asker, "本方案发电用地份额（留空沿用场址值）")
        if generation_share is not None:
            spec["generation_share"] = generation_share
        local_land = _optional_number(asker, "本地发电及配套所需面积 ha（可留空）")
        if local_land is not None:
            spec["local_generation_required_ha"] = local_land
        wue = _optional_number(asker, "本方案 WUE 覆盖（L/kWh IT，可留空）")
        if wue is not None:
            spec["wue_l_per_kwh_it"] = wue

    if kind in {"coal", "gas"}:
        spec["units"] = _number(asker, "可同时运行机组台数", 2 if kind == "coal" else 1,
                                minimum=1, integer=True, allow_zero=False)
        spec["unit_net_mw"] = _number(asker, "单机持续净功率 MW", 80 if kind == "coal" else 60,
                                      minimum=0.000001, allow_zero=False)
        efficiency = _optional_number(asker, "净效率（可留空）")
        if efficiency is not None:
            spec["net_efficiency"] = efficiency
        if kind == "gas":
            spec["gas_supply_adequate"] = _yes_no(asker, "供气是否充足", True)
    elif kind == "wind":
        installed = _optional_number(asker, "风电装机 MW（留空则用面积×密度）")
        if installed is None:
            spec["area_km2"] = _number(asker, "风电合格面积 km²", 10, minimum=0.000001, allow_zero=False)
            spec["density_mw_per_km2"] = _number(asker, "风电装机密度 MW/km²", 8, minimum=0.000001, allow_zero=False)
        else:
            spec["installed_mw"] = installed
        if grid_mw > 0:
            spec["net_output_mw"] = _series(asker, "同期风电净出力 MW（逗号分隔）")
        else:
            use_series = _yes_no(asker, "是否输入同期净出力序列", True)
            if use_series:
                spec["net_output_mw"] = _series(asker, "同期风电净出力 MW（逗号分隔）")
            else:
                spec["alpha"] = _number(asker, "考察期保障比例 alpha", 0.2, minimum=0, maximum=1)
    elif kind == "hydro":
        spec["installed_mw"] = _number(asker, "水电装机 MW", 80, minimum=0, allow_zero=False)
        spec["flow_m3_per_s"] = _number(asker, "可用流量 m³/s", 100, minimum=0, allow_zero=False)
        spec["net_head_m"] = _number(asker, "净落差 m", 100, minimum=0, allow_zero=False)
        spec["efficiency"] = _number(asker, "综合效率", 0.9, minimum=0.000001, maximum=1, allow_zero=False)
    elif kind == "solar":
        spec["area_km2"] = _number(asker, "光伏合格面积 km²", 5, minimum=0.000001, allow_zero=False)
        spec["density_mw_per_km2"] = _number(asker, "光伏装机密度 MW/km²", 100, minimum=0.000001, allow_zero=False)
        spec["dt_hours"] = _number(asker, "时段长度 dt_hours", 1, minimum=0.000001, allow_zero=False)
        spec["net_output_mw"] = _series(asker, "光伏逐时净功率 MW（逗号分隔）")
        battery = _ask_battery(asker, True)
        if battery is not None:
            spec["battery"] = battery
    elif kind == "combined_battery":
        spec["installed_mw"] = _number(asker, "风光合计装机 MW", 230, minimum=0.000001, allow_zero=False)
        spec["dt_hours"] = _number(asker, "时段长度 dt_hours", 1, minimum=0.000001, allow_zero=False)
        spec["supply_series_mw"] = _series(asker, "风光合并逐时净功率 MW（逗号分隔）")
        spec["battery"] = _ask_battery(asker, required=True)
    return spec


def build_interactive_config(asker=input, say=print, default_json=None):
    """收集一套配置，供函数调用和测试复用。"""
    say("IMMC 2027 A 题第一问：交互式容量计算")
    mode = _choice(asker, "计算模式", ["联合模型（电/水/土地）", "仅电力分项"], "联合模型（电/水/土地）")
    joint = mode.startswith("联合")
    data = {}
    if joint:
        data.update(_ask_site(asker))
        data["model"] = "q1"
    data.update(_ask_power_inputs(asker, joint))
    grid_mw = data.get("P_grid_mw", data.get("P_grid_mva", 0) * data.get("power_factor", 1))
    if joint:
        data["water"] = _ask_water(asker)
        data["land"] = _ask_land(asker)
    data["scenarios"] = []
    while True:
        index = len(data["scenarios"]) + 1
        data["scenarios"].append(_ask_scenario(asker, index, joint, grid_mw))
        if not _yes_no(asker, "继续添加方案", False):
            break
    if default_json:
        output_path = str(default_json)
        say(f"JSON 输出：{output_path}")
    else:
        output_path = _text(asker, "JSON 输出路径（留空只显示结果）", allow_blank=True)
    return data, output_path


def run_interactive(asker=input, say=print, default_json=None):
    """运行输入向导，返回进程退出码。"""
    from .cli import _print, calculate

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
