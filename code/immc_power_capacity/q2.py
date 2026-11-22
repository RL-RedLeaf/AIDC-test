"""Q2：同等算力需求下，比较集中式与分布式方案的运行足迹和当地资源压力。"""

from math import fsum, isclose, log

from .core import (
    ValidationError, _cap_generation_by_land, _config_series, _k_factor, _nonnegative, _positive, assess_site,
)


FOOTPRINT = ("carbon_t_co2", "water_m3", "land_ha")
RESOURCES = ("water", "grid", "land")


def _mapping(value, field):
    if not isinstance(value, dict):
        raise ValidationError(f"{field} 需要一个配置对象。")
    return value


def _series(value, field, count):
    values = value if isinstance(value, list) else [value] * count
    if len(values) != count:
        raise ValidationError(f"{field} 需要 {count} 个时段。")
    for item in values:
        _nonnegative(field, item)
    return values


def _weights(value, keys, field):
    if set(_mapping(value, field)) != set(keys):
        raise ValidationError(f"{field} 需要权重 {', '.join(keys)}。")
    for key in keys:
        _nonnegative(f"{field}.{key}", value[key])
    if not isclose(fsum(value.values()), 1.0, abs_tol=1e-9):
        raise ValidationError(f"{field} 的权重之和须为 1。")
    return value


def _fraction(used, available):
    if available == 0:
        return None if used > 0 else 0.0
    return used / available


def _exceeds(used, available):
    return used > available and not isclose(used, available, abs_tol=1e-9)


def _dispatch_limits(spec, row, count, dt):
    """风电和无储能光伏可使用同期出力，其余使用 Q1 可持续净容量。"""
    firm = row["breakdown"]["self_generation_mw"]
    kind = spec["type"]
    if kind != "wind" and row["power_type"] != "solar":
        return [firm] * count
    limited, _, _ = _cap_generation_by_land(kind, spec, row["generation_land_ha"])
    if kind == "solar" and not isclose(spec["dt_hours"], dt):
        raise ValidationError("无储能光伏的出力与任务需要相同 dt_hours。")
    if "net_output_mw" in limited:
        output = _config_series(limited, "net_output_mw", True)
        return _series(list(output), "net_output_mw", count)
    field = "power_ratios" if kind == "wind" else "supply_ratios"
    if field in limited:
        installed = row["method"]["installed_mw"]
        ratios = _config_series(limited, field, True)
        return [installed * ratio for ratio in _series(list(ratios), field, count)]
    return [firm] * count


def _selected_scenario(site, scenario_name):
    name = site.get("site")
    scenarios = site.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValidationError(f"{name} 缺少 Q1 scenarios。")
    selected = [spec for spec in scenarios if isinstance(spec, dict)
                and spec.get("name") == scenario_name]
    if not isinstance(scenario_name, str) or len(selected) != 1:
        raise ValidationError(f"{name} 需要指定唯一的 Q1 scenario。")
    if not isinstance(selected[0].get("type"), str):
        raise ValidationError(f"{name} 的 Q1 方案缺少电源 type。")
    spec = {**selected[0], "type": selected[0]["type"].strip().lower()}
    q1 = assess_site({**site, "scenarios": [spec]})
    return spec, q1["scenarios"][0], q1["water"]

def _operating_periods(node, site, spec, row, water, it_mw, dt, seasons):
    count = len(it_mw)
    name, power = node["site"], row["breakdown"]
    grid_factor = _series(node.get("grid_co2_t_per_mwh"), "grid_co2_t_per_mwh", count)
    self_factor = _series(node.get("self_co2_t_per_mwh", 0 if spec["type"] == "grid" else None),
                          "self_co2_t_per_mwh", count)
    generation_water = spec.get("generation_water_l_per_kwh",
                                water["generation_water_l_per_kwh"].get(spec["type"], 0))
    available_self = _dispatch_limits(spec, row, count, dt)
    multipliers = _series(node.get("operating_k_factor", power["k"]), "operating_k_factor", count)
    for factor in multipliers:
        _k_factor(factor)
    facility = [factor * load for factor, load in zip(multipliers, it_mw)]
    generation = (_series(node["self_generation_mw"], "self_generation_mw", count)
                  if "self_generation_mw" in node else
                  [max(0.0, load - power["grid_mw"]) for load in facility])
    raw_water = site["water"]
    seasonal = "wue_summer_l_per_kwh_it" in raw_water
    if seasonal and seasons is None:
        raise ValidationError(f"{name} 采用季节 WUE，需要逐时段 seasons。")
    periods, issues = [], []
    for index, load in enumerate(facility):
        self_mw = generation[index]
        if _exceeds(self_mw, load):
            raise ValidationError(f"{name} 第 {index + 1} 时段的自供电超过设施负荷。")
        grid_mw = max(0.0, load - self_mw)
        if _exceeds(self_mw, available_self[index]) or _exceeds(grid_mw, power["grid_mw"]):
            issues.append(f"第 {index + 1} 时段供电超过可交付功率")
        season = seasons[index] if seasonal else "design"
        wue = spec.get("wue_l_per_kwh_it", raw_water.get(f"wue_{season}_l_per_kwh_it",
                                                         row["wue_l_per_kwh_it"]))
        rate = wue * it_mw[index] + generation_water * self_mw
        if any(check["period"] == season and _exceeds(rate, check["limit_m3_h"])
               for check in row["water_checks"]):
            issues.append(f"第 {index + 1} 时段超过 Q1 供水预算")
        carbon = (grid_mw * grid_factor[index] + self_mw * self_factor[index]) * dt
        periods.append({"it_mw": it_mw[index], "facility_mw": load, "grid_mw": grid_mw,
                        "self_generation_mw": self_mw, "water_m3_h": rate, "carbon_t_co2": carbon})
    volume = fsum(period["water_m3_h"] for period in periods) * dt
    if "period_budget_m3" in raw_water and _exceeds(volume, raw_water["period_budget_m3"]):
        issues.append("统计期用水量超过 Q1 总量预算")
    return periods, volume, issues


def _node_result(node, sites, count, dt, seasons):
    name = node.get("site")
    if not isinstance(name, str) or name not in sites:
        raise ValidationError(f"未知 Q2 场址 {name}。")
    site = _mapping(sites[name], name)
    spec, row, water = _selected_scenario(site, node.get("scenario"))
    compute = _series(node.get("compute"), "compute", count)
    efficiency = node.get("compute_per_mw_it")
    _positive("compute_per_mw_it", efficiency)
    it_mw = [rate / efficiency for rate in compute]
    installed = node.get("installed_it_mw", max(it_mw))
    _nonnegative("installed_it_mw", installed)
    periods, volume, issues = _operating_periods(node, site, spec, row, water, it_mw, dt, seasons)
    if _exceeds(max(it_mw), installed):
        issues.append("任务峰值超过建成 IT 容量")
    if _exceeds(installed, row["P_mw_it"]):
        issues.append("建成 IT 容量超过所选 Q1 配置的联合上限")
    land = row["land"]
    site_area = land["fixed_it_ha"] + row["generation_land_ha"] + site["land"]["ha_per_mw_it"] * installed
    external_default = row["generation_land_required_ha"] if spec.get("generation_land_in_site") is False else 0
    external_area = node.get("external_generation_land_ha", external_default)
    _nonnegative("external_generation_land_ha", external_area)
    grid_limit = node.get("local_grid_available_mw")
    _nonnegative("local_grid_available_mw", grid_limit)
    water_limit = node.get("local_water_available_m3_h", water["limits_m3_h"].get("source"))
    local_water = _series(water_limit, "local_water_available_m3_h", count)
    water_ratios = [_fraction(period["water_m3_h"], available) for period, available in zip(periods, local_water)]
    grid_ratio = _fraction(max(period["grid_mw"] for period in periods), grid_limit)
    emissions = fsum(period["carbon_t_co2"] for period in periods)
    pressure = {"water": None if None in water_ratios else max(water_ratios),
                "grid": grid_ratio, "land": _fraction(site_area, land["site_ha"])}
    for resource, ratio in pressure.items():
        if ratio is None or ratio >= 1:
            issues.append(f"{resource} 达到或超过当地可用上限")
    return {
        "site": name, "q1_site": site["site"], "scenario": spec["name"], "assessment_year": site["assessment_year"],
        "compute": compute, "installed_it_mw": installed, "q1_capacity_mw_it": row["P_mw_it"],
        "q1_binding": row["binding"], "water_basis": water["basis"], "periods": periods,
        "footprint": {"carbon_t_co2": emissions, "water_m3": volume, "land_ha": site_area + external_area},
        "site_area_ha": site_area, "external_generation_land_ha": external_area,
        "pressure": pressure, "grid_remaining_fraction": None if grid_ratio is None else 1 - grid_ratio,
        "infeasible_reasons": issues,
    }


def _plan_result(kind, plan, sites, demand, dt, seasons):
    nodes = _mapping(plan, kind).get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValidationError(f"{kind}.nodes 需要非空节点列表。")
    if (kind == "centralized" and len(nodes) != 1) or (kind == "distributed" and len(nodes) < 2):
        raise ValidationError("centralized 需要一个节点，distributed 至少需要两个节点。")
    rows = [_node_result(_mapping(node, "node"), sites, len(demand), dt, seasons) for node in nodes]
    if len({row["q1_site"] for row in rows}) != len(rows):
        raise ValidationError("同一方案不能重复计入同一场址的资源。")
    for index, target in enumerate(demand):
        if not isclose(fsum(row["compute"][index] for row in rows), target, abs_tol=1e-9):
            raise ValidationError(f"{kind} 第 {index + 1} 时段分配的算力与总需求不符。")
    network = _mapping(plan.get("wan", {}), "wan")
    if network.keys() - {"power_mw", "co2_t_per_mwh"}:
        raise ValidationError("wan 仅接受 power_mw 和 co2_t_per_mwh。")
    wan_power = _series(network.get("power_mw", 0), "wan.power_mw", len(demand))
    wan_factor = _series(network.get("co2_t_per_mwh", None if any(wan_power) else 0),
                         "wan.co2_t_per_mwh", len(demand))
    wan_carbon = fsum(power * factor for power, factor in zip(wan_power, wan_factor)) * dt
    totals = {key: fsum(row["footprint"][key] for row in rows) for key in FOOTPRINT}
    totals["carbon_t_co2"] += wan_carbon
    per_day = 24 / (dt * len(demand))
    daily = {"carbon_kg_co2_per_day": totals["carbon_t_co2"] * 1000 * per_day,
             "water_kg_per_day": totals["water_m3"] * 1000 * per_day}
    pressure, hotspots = {}, {}
    for resource in RESOURCES:
        ratios = [row["pressure"][resource] for row in rows]
        maximum = None if None in ratios else max(ratios)
        pressure[resource] = maximum
        hotspots[resource] = [row["site"] for row, ratio in zip(rows, ratios)
                              if ratio == maximum or (ratio is not None and maximum is not None
                                                      and isclose(ratio, maximum, abs_tol=1e-12))]
    return {"nodes": rows, "footprint": totals, "daily_average": daily, "pressure": pressure, "hotspots": hotspots,
            "wan_mwh": fsum(wan_power) * dt, "wan_carbon_t_co2": wan_carbon,
            "feasible": not any(row["infeasible_reasons"] for row in rows)}


def assess_network(data):
    """比较逐时段完成同一算力需求的两种既定节点分配，返回可写入 JSON 的报告。"""
    sites = _mapping(data.get("sites"), "sites")
    demand = data.get("compute_demand")
    if not isinstance(demand, list) or not demand:
        raise ValidationError("compute_demand 需要非空的逐时段算力需求。")
    _series(demand, "compute_demand", len(demand))
    if not any(demand):
        raise ValidationError("统计期总算力需求须大于零。")
    dt = data.get("dt_hours")
    _positive("dt_hours", dt)
    seasons = data.get("seasons")
    if seasons is not None and (not isinstance(seasons, list) or len(seasons) != len(demand)
                                or any(item not in ("summer", "winter") for item in seasons)):
        raise ValidationError("seasons 需要为各时段指定 summer 或 winter。")
    weights = _weights(data.get("footprint_weights"), FOOTPRINT, "footprint_weights")
    penalties = _weights(data.get("pressure_weights"), RESOURCES, "pressure_weights")
    multiplier = data.get("lambda")
    _nonnegative("lambda", multiplier)
    plans = {kind: _plan_result(kind, data.get(kind), sites, demand, dt, seasons)
             for kind in ("centralized", "distributed")}
    rows = [row for plan in plans.values() for row in plan["nodes"]]
    if len({row["assessment_year"] for row in rows}) != 1 or len({row["water_basis"] for row in rows}) != 1:
        raise ValidationError("各场址须采用同一评估年份和用水口径。")
    reference = _mapping(data.get("reference_footprint", plans["centralized"]["footprint"]), "reference_footprint")
    for key, weight in weights.items():
        if weight:
            _positive(f"reference_footprint.{key}（正权重项需正基准）", reference.get(key))
    for plan in plans.values():
        relative = fsum(weight * plan["footprint"][key] / reference[key] for key, weight in weights.items() if weight)
        plan["F"] = log(relative) if relative > 0 else None
        plan["S"] = plan["omega"] = None
        if plan["feasible"]:
            plan["S"] = fsum(penalties[key] * ratio / (1 - ratio) for key, ratio in plan["pressure"].items())
            if plan["F"] is not None:
                plan["omega"] = plan["F"] + multiplier * plan["S"]
    feasible = [kind for kind, plan in plans.items() if plan["feasible"]]
    # log(0) 的极限为负无穷，只用于排序，JSON 中用 null 与状态字段表示。
    scores = {kind: plans[kind]["omega"] if plans[kind]["omega"] is not None else float("-inf") for kind in feasible}
    best = min(scores.values(), default=None)
    winners = [kind for kind, value in scores.items() if isclose(value, best, abs_tol=1e-10)]
    return {"model": "q2", "inputs": data, "assessment_year": rows[0]["assessment_year"],
            "water_basis": rows[0]["water_basis"], "hours": len(demand) * dt,
            "reference_footprint": reference, "plans": plans, "winners": winners}
