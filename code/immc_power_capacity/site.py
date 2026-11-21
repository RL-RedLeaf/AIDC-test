"""正稿 Q1：在同一场址、设计期和服务水平下比较建成配置。"""

from copy import deepcopy
from math import isclose

from .exceptions import ValidationError
from .model import total_capacity
from .supply import _build_scenario
from .validators import _efficiency, _nonnegative, _positive, _positive_integer, _ratio


def water_budget(water):
    """式 (8)–(10)，流量统一为 m³/h。"""
    basis = water.get("basis")
    if basis not in ("withdrawal", "consumption"):
        raise ValidationError("water.basis 应为 withdrawal（取水）或 consumption（耗水）。")
    allowed = {"basis", "source_m3_h", "stress_m3_h", "policy_m3_h", "river_m3_h",
               "eco_m3_h", "other_m3_h", "stress_fraction", "wue_l_per_kwh_it", "period_budget"}
    if unknown := water.keys() - allowed:
        raise ValidationError(f"water 含未识别字段：{', '.join(map(str, unknown))}")
    limits = {}
    for key in ("source", "stress", "policy"):
        field = f"{key}_m3_h"
        if field in water:
            _nonnegative(field, water[field])
            limits[key] = water[field]
    river_fields = ("river_m3_h", "eco_m3_h", "other_m3_h")
    if any(field in water for field in (*river_fields, "stress_fraction")):
        if basis != "withdrawal":
            raise ValidationError("式 (9)、(10) 的既有取水和水压力需使用 withdrawal 口径。")
        for field in river_fields:
            _nonnegative(field, water.get(field))
        available = water["river_m3_h"] - water["eco_m3_h"]
        if "source" in limits:
            raise ValidationError("水源上限应选用直接给定或式 (9) 推算中的一种。")
        limits["source"] = max(0.0, available - water["other_m3_h"])
        if "stress_fraction" in water:
            if "stress" in limits:
                raise ValidationError("水压力上限应选用直接给定或式 (10) 推算中的一种。")
            _ratio("stress_fraction", water["stress_fraction"])
            limits["stress"] = max(0.0, water["stress_fraction"] * available - water["other_m3_h"])
    period = water.get("period_budget")
    if period is not None:
        if not isinstance(period, dict) or period.get("limit") not in ("source", "stress", "policy"):
            raise ValidationError("period_budget.limit 需说明总量属于 source、stress 或 policy。")
        key = period["limit"]
        if key in limits:
            raise ValidationError(f"同一水量上限 {key} 重复输入。")
        _nonnegative("volume_m3", period.get("volume_m3"))
        _positive("hours", period.get("hours"))
        _efficiency("it_load_factor", period.get("it_load_factor"))
        limits[key] = period["volume_m3"] / period["hours"]
    if not limits:
        raise ValidationError("水量资料不足，source、stress、policy 至少需一个可用上限。")
    design_limits = limits.copy()
    if period:
        design_limits[period["limit"]] /= period["it_load_factor"]
    return {
        "basis": basis, "limits_m3_h": limits, "Q_max_m3_h": min(limits.values()),
        "design_equivalent_m3_h": min(design_limits.values()),
        "period_budget": period,
        "omitted": [key for key in ("source", "stress", "policy") if key not in limits],
    }


def land_capacity(land, share):
    """式 (12)–(15)，面积为 ha，强度为 ha/MW IT。"""
    area = land.get("effective_ha")
    fixed = land.get("fixed_it_ha", 0)
    intensity = land.get("ha_per_mw_it")
    _nonnegative("effective_ha", area)
    _nonnegative("fixed_it_ha", fixed)
    _positive("ha_per_mw_it", intensity)
    _ratio("generation_share", share)
    site_area = area * (1 - share)
    return {
        "site_ha": site_area, "reserved_generation_ha": area * share,
        "fixed_it_ha": fixed, "optimistic_zero_fixed": fixed == 0,
        "P_L_mw_it": max(0.0, site_area - fixed) / intensity,
    }


def _grid(data):
    if ("P_grid_mw" in data) == ("P_grid_mva" in data):
        raise ValidationError("电网需给 P_grid_mw 或 P_grid_mva 中的一项。")
    if "P_grid_mva" in data:
        _nonnegative("P_grid_mva", data["P_grid_mva"])
        _efficiency("power_factor", data.get("power_factor"))
        return data["P_grid_mva"] * data["power_factor"], "MVA × 功率因数，初筛上界"
    _nonnegative("P_grid_mw", data["P_grid_mw"])
    return data["P_grid_mw"], "接入点持续净有功"


def _resource_row(data, spec, grid, budget):
    kind = spec.get("type")
    if not isinstance(kind, str):
        raise ValidationError("每套配置需要 type。")
    if kind == "wind" and grid > 0 and "alpha" in spec:
        raise ValidationError("并网风电需同期 net_output_mw 或 power_ratios 进行逐时平衡。")
    multiplier = spec.get("k_factor", data.get("k_factor"))
    row = _build_scenario(kind, spec, grid, multiplier, spec["name"])
    pcc = spec.get("C_PCC_mw", data.get("C_PCC_mw"))
    if pcc != "dedicated":
        _nonnegative("C_PCC_mw（专用接线填 dedicated）", pcc)
    breakdown = row["breakdown"]
    electric, facility = total_capacity(grid, breakdown["self_generation_mw"], multiplier,
                                        None if pcc == "dedicated" else pcc)
    breakdown.update(it_mw=electric, facility_mw=facility, C_PCC_mw=pcc)
    if kind == "wind":
        row["method"]["capacity_basis"] = "恒定可交付电网与风电的逐时平衡" if grid else "孤立恒载最低出力"

    wue = spec.get("wue_l_per_kwh_it", data["water"].get("wue_l_per_kwh_it"))
    _nonnegative("wue_l_per_kwh_it", wue)
    water_limit = budget["design_equivalent_m3_h"] / wue if wue > 0 else None
    share = spec.get("generation_share", data["land"].get("generation_share"))
    land = land_capacity(data["land"], share)
    limits = {"电力": electric, "土地": land["P_L_mw_it"]}
    if water_limit is not None:
        limits["水"] = water_limit
    capacity = min(limits.values())
    row.update(name=spec["name"], online_year=spec["online_year"], land=land,
               wue_l_per_kwh_it=wue, P_E_mw_it=electric, P_W_mw_it=water_limit,
               P_L_mw_it=land["P_L_mw_it"], P_mw_it=capacity,
               binding=[key for key, value in limits.items() if isclose(value, capacity, abs_tol=1e-9)])
    return row


def assess_site(data):
    for key in ("site", "period_note", "service_level"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValidationError(f"场址评估需填写 {key}。")
    year = data.get("assessment_year")
    _positive_integer("assessment_year", year)
    for key in ("water", "land"):
        if not isinstance(data.get(key), dict):
            raise ValidationError(f"场址评估需要 {key} 的参数。")
    grid, grid_basis = _grid(data)
    budget = water_budget(data["water"])
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValidationError("scenarios 至少要有一套配置。")
    rows, excluded, names = [], [], set()
    for spec in scenarios:
        if not isinstance(spec, dict) or not isinstance(spec.get("name"), str) or not spec["name"].strip():
            raise ValidationError("每套配置需要 name。")
        if spec["name"] in names:
            raise ValidationError(f"配置名称重复：{spec['name']}")
        names.add(spec["name"])
        _positive_integer("online_year", spec.get("online_year"))
        if spec["online_year"] > year:
            excluded.append({"name": spec["name"], "online_year": spec["online_year"], "reason": "尚未投运"})
            continue
        row = _resource_row(data, spec, grid, budget)
        if "local_generation_required_ha" in spec:
            required = spec["local_generation_required_ha"]
            _nonnegative("local_generation_required_ha", required)
            if required > row["land"]["reserved_generation_ha"] + 1e-9:
                excluded.append({"name": spec["name"], "online_year": spec["online_year"],
                                 "reason": "本地发电及配套用地不足"})
                continue
        rows.append(row)
    if not rows:
        raise ValidationError(f"{year} 年没有满足投运与发电用地条件的候选配置。")
    best = max(row["P_mw_it"] for row in rows)
    return {
        "site": data["site"], "assessment_year": year, "period_note": data["period_note"],
        "inputs": {key: value for key, value in data.items() if key != "sensitivity"},
        "service_level": data["service_level"], "grid_basis": grid_basis, "water": budget,
        "scenarios": rows, "excluded": excluded, "P_max_mw_it": best,
        "winners": [row["name"] for row in rows if isclose(row["P_mw_it"], best, abs_tol=1e-9)],
    }


def sensitivity_cases(data):
    """§7.5，每次只替换一个显式的场址参数，以同一组配置重算。"""
    allowed = {"P_grid_mw", "C_PCC_mw", "k_factor", "water.wue_l_per_kwh_it",
               "water.stress_fraction", "land.effective_ha", "land.ha_per_mw_it",
               "land.generation_share"}
    cases = []
    settings = data.get("sensitivity", {})
    if not isinstance(settings, dict):
        raise ValidationError("sensitivity 应为参数与取值列表。")
    for field, values in settings.items():
        if field not in allowed or not isinstance(values, list) or not values:
            raise ValidationError(f"无效的敏感性参数或取值列表：{field}")
        for value in values:
            varied = deepcopy(data)
            path = field.split(".")
            section = varied if len(path) == 1 else varied[path[0]]
            if path[-1] not in section:
                raise ValidationError(f"敏感性参数 {field} 缺少基准值。")
            section[path[-1]] = value
            report = assess_site(varied)
            cases.append({"parameter": field, "value": value, "P_max_mw_it": report["P_max_mw_it"],
                          "winners": report["winners"], "scenarios": [
                              {"name": row["name"], "P_mw_it": row["P_mw_it"], "binding": row["binding"]}
                              for row in report["scenarios"]]})
    return cases
