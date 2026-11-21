"""Q1 联合容量模型和兼容的电力分项计算核心。"""

import importlib
import math
from math import isclose

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, eye, hstack


class CapacityModelError(ValueError):
    """输入数据不足或无法求解时的基础异常."""


class ValidationError(CapacityModelError):
    """模型输入不满足单位、范围或完整性要求."""


class InfeasibleError(CapacityModelError):
    """光储问题无可行运行安排."""


def _finite_number(field, value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError(f"{field} 必须是数值。")
    if not math.isfinite(value):
        raise ValidationError(f"{field} 必须是有限数值。")


def _positive(field, value):
    _finite_number(field, value)
    if value <= 0:
        raise ValidationError(f"{field} 必须为正数。")


def _nonnegative(field, value):
    _finite_number(field, value)
    if value < 0:
        raise ValidationError(f"{field} 不能为负。")


def _ratio(field, value):
    _nonnegative(field, value)
    if value > 1:
        raise ValidationError(f"{field} 必须位于 [0, 1]。")


def _efficiency(field, value):
    _finite_number(field, value)
    if not (0 < value <= 1):
        raise ValidationError(f"{field} 必须位于 (0, 1]。")


def _positive_integer(field, value):
    _finite_number(field, value)
    if value <= 0 or not float(value).is_integer():
        raise ValidationError(f"{field} 必须是正整数（机组台数）。")


def _k_factor(value):
    _finite_number("k_factor", value)
    if value < 1:
        raise ValidationError("k_factor 不能小于 1。")


def _finite_nonnegative(values, field):
    if values is None:
        raise ValidationError(f"{field} 不能缺失。")
    try:
        series = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} 必须是数值序列。") from exc
    if series.ndim != 1 or series.size == 0:
        raise ValidationError(f"{field} 必须是非空的一维数值序列。")
    if not np.all(np.isfinite(series)) or np.any(series < 0):
        raise ValidationError(f"{field} 必须为无缺失的非负数值。")
    return series


def total_capacity(grid_mw, self_generation_mw, k_factor):
    """权威稿式 (1)、(6)：P_total=P_grid+P_self，P_E=P_total/k。"""
    _nonnegative("P_grid", grid_mw)
    _nonnegative("P_self", self_generation_mw)
    _k_factor(k_factor)
    facility_mw = grid_mw + self_generation_mw
    return facility_mw / k_factor, facility_mw


def _storage_series(values):
    try:
        array = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValidationError("光储供电序列必须是数值数组。") from exc
    if array.ndim != 1:
        raise ValidationError("光储供电序列必须是一维数组。")
    if not np.all(np.isfinite(array)) or np.any(array < 0):
        raise ValidationError("光储供电序列必须为无缺失的非负功率。")
    return array


def _schedule_without_battery(supply):
    level = float(supply.min())
    return {
        "L_mw": level,
        "charge_mw": [0.0] * supply.size,
        "discharge_mw": [0.0] * supply.size,
        "energy_start_mwh": [0.0] * supply.size,
        "curtailment_mw": (supply - level).tolist(),
        "direction": [0] * supply.size,
        "status": "no battery",
    }


def solve_storage_capacity(supply, dt, charge_max, discharge_max, usable_energy,
                           charge_efficiency, discharge_efficiency):
    """用稀疏 LP 求周期恒载，再以相同的电量轨迹重建单方向调度。"""
    supply = _storage_series(supply)
    _positive("dt_hours", dt)
    _nonnegative("C_max", charge_max)
    _nonnegative("D_max", discharge_max)
    _nonnegative("E_usable", usable_energy)
    _efficiency("charge_efficiency", charge_efficiency)
    _efficiency("discharge_efficiency", discharge_efficiency)
    if not supply.size:
        raise ValidationError("光储供电序列不能为空。")
    if not charge_max or not discharge_max or not usable_energy:
        return float(supply.min()), _schedule_without_battery(supply)

    periods = supply.size
    identity = eye(periods, format="csr")
    indices = np.arange(periods)
    successor = csr_matrix((np.ones(periods), (indices, (indices + 1) % periods)),
                           shape=(periods, periods))
    zero_column = csr_matrix((periods, 1))
    power = hstack([np.ones((periods, 1)), identity, -identity, csr_matrix(identity.shape)], format="csr")
    energy_balance = hstack([zero_column, -dt * charge_efficiency * identity,
                             dt / discharge_efficiency * identity, successor - identity], format="csr")
    bounds = ([(0, None)] + [(0, charge_max)] * periods + [(0, discharge_max)] * periods
              + [(0, usable_energy)] * periods)
    objective = np.zeros(1 + 3 * periods)
    objective[0] = -1
    constraints = dict(A_ub=power, b_ub=supply, A_eq=energy_balance, b_eq=np.zeros(periods),
                       method="highs")
    result = linprog(objective, bounds=bounds, **constraints)
    if not result.success:
        raise InfeasibleError(f"光储容量求解失败：{result.message}")

    load = float(result.x[0])
    bounds[0] = (load, load)
    objective[0] = 0
    objective[1 + 2 * periods] = 1
    result = linprog(objective, bounds=bounds, **constraints)
    if not result.success:
        raise InfeasibleError(f"光储调度重建失败：{result.message}")
    charge, discharge, energy = np.split(result.x[1:], 3)
    stored_mw = charge_efficiency * charge - discharge / discharge_efficiency
    charge = np.maximum(stored_mw, 0) / charge_efficiency
    discharge = np.maximum(-stored_mw, 0) * discharge_efficiency
    curtail = supply + discharge - load - charge
    if np.min(curtail) < -1e-7 or not np.allclose(
            np.roll(energy, -1), energy + dt * stored_mw, atol=1e-7, rtol=1e-9):
        raise InfeasibleError("光储调度未通过功率余量或周期电量校核。")
    return load, {
        "L_mw": load, "charge_mw": charge.tolist(), "discharge_mw": discharge.tolist(),
        "energy_start_mwh": energy.tolist(), "curtailment_mw": np.maximum(curtail, 0).tolist(),
        "direction": (charge > 0).astype(int).tolist(), "status": result.message,
    }


def grid_only(grid_mw, k_factor):
    """纯电网方案：P_self=0."""
    _nonnegative("P_grid", grid_mw)
    _k_factor(k_factor)
    return _breakdown(grid_mw, 0.0, k_factor, "grid_only", {
        "equation": "正文式(1)、(6)",
        "assumption": "P_self = 0，作为所有候选方案的基准。",
    })


def thermal(name, grid_mw, k_factor, units, unit_net_mw,
            net_efficiency=None, gas_supply_adequate=None):
    """煤电或燃气：P_j=N_j p_j^net，正文式(2)。"""
    _nonnegative("P_grid", grid_mw)
    _k_factor(k_factor)
    key = str(name).strip().lower()
    if key not in {"coal", "gas"}:
        raise ValidationError("thermal 电源名必须是 coal 或 gas。")
    _positive_integer("units", units)
    _positive("unit_net_mw", unit_net_mw)
    if net_efficiency is not None:
        _efficiency("net_efficiency", net_efficiency)
    if key == "gas" and gas_supply_adequate is False:
        raise ValidationError("燃气方案声明供气不足，不能作为正常运行的容量上界。")

    self_generation = units * unit_net_mw
    if key == "gas":
        gas_note = (
            "declared adequate"
            if gas_supply_adequate is True
            else "未声明；按设计供气充足上界计算"
        )
    else:
        gas_note = None
    return _breakdown(grid_mw, self_generation, k_factor, key, {
        "equation": "正文式(2)",
        "units": int(units),
        "unit_net_mw": unit_net_mw,
        "fuel_heat_needed_mw": (
            None if net_efficiency is None else self_generation / net_efficiency
        ),
        "gas_supply": gas_note,
    })


def wind(name, grid_mw, k_factor, area_km2=None, density_mw_per_km2=None,
         alpha=None, power_ratios=None, net_output_mw=None, installed_mw=None):
    """风电：P_wind=alpha_wind X_wind，正文式(3)。

    alpha、归一化序列或原始 MW 序列三选一。年度容量因子不进入本式。
    """
    _nonnegative("P_grid", grid_mw)
    _k_factor(k_factor)
    if sum(item is not None for item in (alpha, power_ratios, net_output_mw)) != 1:
        raise ValidationError("风电的 alpha、power_ratios、net_output_mw 必须且只能提供一个。")

    if installed_mw is None:
        if area_km2 is None or density_mw_per_km2 is None:
            raise ValidationError("风电需要 area_km2 与 density_mw_per_km2，或直接给 installed_mw。")
        _positive("A_wind", area_km2)
        _positive("rho_wind", density_mw_per_km2)
        installed_mw = area_km2 * density_mw_per_km2
    else:
        _nonnegative("installed_mw", installed_mw)

    if alpha is not None:
        _ratio("alpha", alpha)
        alpha_value = float(alpha)
        source = "provided"
    else:
        if alpha is None and power_ratios is None:
            series = _finite_nonnegative(net_output_mw, "net_output_mw")
            if installed_mw <= 0:
                raise ValidationError("用 net_output_mw 计算 alpha 时，installed_mw 必须大于 0。")
            alpha_value = float(series.min() / installed_mw)
            source = "period minimum net output / installed capacity"
        else:
            series = _finite_nonnegative(power_ratios, "power_ratios")
            alpha_value = float(series.min())
            source = "period minimum normalized net output"

    if alpha_value > 1 + 1e-12:
        raise ValidationError(
            "风电 alpha 必须在 [0,1]；请检查装机、出力序列及其单位（MW 或 MWh/MWh）。"
        )
    capacity = installed_mw * alpha_value
    return _breakdown(grid_mw, capacity, k_factor, "wind", {
        "equation": "正文式(3)",
        "installed_mw": installed_mw,
        "alpha": alpha_value,
        "alpha_source": source,
    })


def hydro(name, grid_mw, k_factor, installed_mw, flow_m3_per_s, net_head_m, efficiency):
    """水电：正文式(4)，流量与落差必须采用同一约束期口径。"""
    _nonnegative("P_grid", grid_mw)
    _k_factor(k_factor)
    _nonnegative("installed_mw", installed_mw)
    _nonnegative("flow_m3_per_s", flow_m3_per_s)
    _nonnegative("net_head_m", net_head_m)
    _efficiency("hydraulic_efficiency", efficiency)
    water_power = 0.00981 * efficiency * flow_m3_per_s * net_head_m
    capacity = min(installed_mw, water_power)
    return _breakdown(grid_mw, capacity, k_factor, "hydro", {
        "equation": "正文式(4)",
        "installed_mw": installed_mw,
        "water_power_mw": water_power,
    })


def solar(name, grid_mw, k_factor, area_km2, density_mw_per_km2,
          supply_ratios=None, dt_hours=None, battery=None, net_output_mw=None):
    """光伏与光储的逐时容量：正文式(5)，附录 A 给出 LP。

    supply_ratios 的单位为 MWh/MWh（净电功率/装机），net_output_mw 为 MW。
    """
    _nonnegative("P_grid", grid_mw)
    _k_factor(k_factor)
    _positive("area_km2", area_km2)
    _positive("density_mw_per_km2", density_mw_per_km2)
    _positive("dt_hours", dt_hours)
    installed_mw = area_km2 * density_mw_per_km2
    if sum(item is not None for item in (supply_ratios, net_output_mw)) != 1:
        raise ValidationError("光伏必须且只能提供 supply_ratios 或 net_output_mw 之一。")
    if net_output_mw is not None:
        values = _finite_nonnegative(net_output_mw, "net_output_mw") / installed_mw
        input_unit = "net_output_mw"
    else:
        values = _finite_nonnegative(supply_ratios, "supply_ratios")
        input_unit = "supply_ratios"

    settings = _battery_settings(battery, required=False)
    self_generation, schedule = solve_storage_capacity(
        installed_mw * values, dt_hours,
        settings["C_max_mw"], settings["D_max_mw"], settings["E_usable_mwh"],
        settings["charge_efficiency"], settings["discharge_efficiency"],
    )
    has_battery = settings["C_max_mw"] > 0
    return _breakdown(
        grid_mw, self_generation, k_factor,
        "solar_storage" if has_battery else "solar",
        {
            "equation": "正文式(5)；附录 A 光储 LP" if has_battery else "正文式(5) 无电池退化（周期最小净功率）",
            "installed_mw": installed_mw,
            "dt_hours": dt_hours,
            "input_series": input_unit,
            "battery": settings if has_battery else None,
            **schedule,
        },
    )


def combined_battery(name, grid_mw, k_factor, supply_series_mw, installed_mw,
                     dt_hours, battery):
    """风光共用电池：先合并同一时段的可用净功率，再求解一次附录 A."""
    _nonnegative("P_grid", grid_mw)
    _k_factor(k_factor)
    _positive("combined_installed_mw", installed_mw)
    _positive("dt_hours", dt_hours)
    values = _finite_nonnegative(supply_series_mw, "supply_series_mw")
    settings = _battery_settings(battery, required=True)
    self_generation, schedule = solve_storage_capacity(
        values, dt_hours,
        settings["C_max_mw"], settings["D_max_mw"], settings["E_usable_mwh"],
        settings["charge_efficiency"], settings["discharge_efficiency"],
    )
    return _breakdown(grid_mw, self_generation, k_factor, "combined_renewables", {
        "equation": "权威稿风、光共用电池；附录 A",
        "installed_mw": installed_mw,
        "dt_hours": dt_hours,
        "input_series": "supply_series_mw",
        "battery": settings,
        **schedule,
    })


def _battery_settings(value, required):
    if value is None:
        if required:
            raise ValidationError("该方案必须提供 battery 配置。")
        return {
            "C_max_mw": 0.0,
            "D_max_mw": 0.0,
            "E_usable_mwh": 0.0,
            "charge_efficiency": 1.0,
            "discharge_efficiency": 1.0,
        }
    if not isinstance(value, dict):
        raise ValidationError("battery 必须是对象。")
    allowed = {
        "C_max_mw", "D_max_mw", "E_usable_mwh",
        "charge_efficiency", "discharge_efficiency",
    }
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValidationError(f"battery 含有未支持字段：{', '.join(unknown)}。")
    for field in ("C_max_mw", "D_max_mw", "E_usable_mwh"):
        if field not in value:
            raise ValidationError(f"battery 缺少字段 {field}。")
    settings = {
        "C_max_mw": value["C_max_mw"],
        "D_max_mw": value["D_max_mw"],
        "E_usable_mwh": value["E_usable_mwh"],
        "charge_efficiency": value.get("charge_efficiency", 1.0),
        "discharge_efficiency": value.get("discharge_efficiency", 1.0),
    }
    _positive("C_max_mw", settings["C_max_mw"])
    _positive("D_max_mw", settings["D_max_mw"])
    _positive("E_usable_mwh", settings["E_usable_mwh"])
    _efficiency("charge_efficiency", settings["charge_efficiency"])
    _efficiency("discharge_efficiency", settings["discharge_efficiency"])
    return settings


def _breakdown(grid_mw, self_generation, k_factor, power_type, method):
    it_mw, facility_mw = total_capacity(grid_mw, self_generation, k_factor)
    return {
        "name": power_type,
        "power_type": power_type,
        "breakdown": {
            "grid_mw": grid_mw,
            "self_generation_mw": self_generation,
            "facility_mw": facility_mw,
            "k": k_factor,
            "it_mw": it_mw,
        },
        "method": method,
    }


def _config_series(spec, field, required):
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


def _config_number(spec, field):
    if field not in spec or spec[field] is None:
        raise CapacityModelError(f"{field} 不能缺失。")
    value = spec[field]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise CapacityModelError(f"{field} 必须是数值。")
    return value


def _config_optional(spec, field):
    return None if field not in spec or spec[field] is None else _config_number(spec, field)


def _build_scenario(kind, spec, grid_value, k_value, name):
    if kind == "grid":
        return grid_only(grid_value, k_value)
    if kind == "coal":
        return thermal(
            "coal", grid_value, k_value,
            _config_number(spec, "units"), _config_number(spec, "unit_net_mw"),
            _config_optional(spec, "net_efficiency"),
        )
    if kind == "gas":
        return thermal(
            "gas", grid_value, k_value,
            _config_number(spec, "units"), _config_number(spec, "unit_net_mw"),
            _config_optional(spec, "net_efficiency"), spec.get("gas_supply_adequate"),
        )
    if kind == "wind":
        return _wind_result(spec, grid_value, k_value)
    if kind == "hydro":
        return hydro(
            name, grid_value, k_value,
            _config_number(spec, "installed_mw"), _config_number(spec, "flow_m3_per_s"),
            _config_number(spec, "net_head_m"), _config_number(spec, "efficiency"),
        )
    if kind == "solar":
        return _solar_result(spec, grid_value, k_value)
    if kind == "combined_battery":
        return combined_battery(
            name, grid_value, k_value,
            _config_series(spec, "supply_series_mw", required=True),
            _config_number(spec, "installed_mw"), _config_number(spec, "dt_hours"),
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
    series = _config_series(spec, source, required=False) if source != "alpha" else None
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
        _config_number(spec, "area_km2"), _config_number(spec, "density_mw_per_km2"),
        supply_ratios=_config_series(spec, source, required=True) if source == "supply_ratios" else None,
        net_output_mw=_config_series(spec, source, required=True) if source == "net_output_mw" else None,
        dt_hours=_config_number(spec, "dt_hours"),
        battery=spec.get("battery"),
    )


Q1_TYPES = frozenset({"grid", "coal", "gas", "wind", "hydro", "solar", "combined_battery"})


def _resolve_wue(water):
    direct = water.get("wue_l_per_kwh_it")
    seasonal_keys = (
        "wue_summer_l_per_kwh_it",
        "wue_winter_l_per_kwh_it",
        "summer_hours",
        "winter_hours",
    )
    provided = [key for key in seasonal_keys if key in water]
    if direct is not None and provided:
        raise ValidationError("WUE 应使用直接值或季节加权值中的一种。")
    if direct is not None:
        _nonnegative("wue_l_per_kwh_it", direct)
        return direct
    if len(provided) != len(seasonal_keys):
        raise ValidationError("季节 WUE 需要同时提供夏季/冬季 WUE 与运行小时数。")
    for key in seasonal_keys[:2]:
        _nonnegative(key, water[key])
    for key in seasonal_keys[2:]:
        _positive(key, water[key])
    total_hours = water["summer_hours"] + water["winter_hours"]
    return (
        water["summer_hours"] * water["wue_summer_l_per_kwh_it"]
        + water["winter_hours"] * water["wue_winter_l_per_kwh_it"]
    ) / total_hours


def water_budget(water):
    """水资源模型，流量统一为 m³/h；WUE 为 L/kWh IT。"""
    basis = water.get("basis")
    if basis not in ("withdrawal", "consumption"):
        raise ValidationError("water.basis 应为 withdrawal（取水）或 consumption（耗水）。")
    allowed = {
        "basis", "source_m3_h", "stress_m3_h", "policy_m3_h", "river_m3_h",
        "eco_m3_h", "other_m3_h", "stress_fraction", "wue_l_per_kwh_it",
        "wue_summer_l_per_kwh_it", "wue_winter_l_per_kwh_it",
        "summer_hours", "winter_hours", "generation_water_l_per_kwh",
    }
    if unknown := water.keys() - allowed:
        raise ValidationError(f"water 含未识别字段：{', '.join(map(str, unknown))}")
    wue = _resolve_wue(water)
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
        missing = [field for field in river_fields if field not in water]
        if missing:
            raise ValidationError(
                "仅有河流流量和生态保留只能得到未核实的 Q_水文余量，不能作为 "
                "Q_source；请补充 other_m3_h，或直接提供 source_m3_h / 供水单位交付量。"
            )
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
    if not limits:
        raise ValidationError("水量资料不足，source、stress、policy 至少需一个可用上限。")
    coefficients = water.get("generation_water_l_per_kwh", {})
    if not isinstance(coefficients, dict):
        raise ValidationError("generation_water_l_per_kwh 必须是对象。")
    allowed_coefficients = {"coal", "gas", "wind", "solar", "combined_battery"}
    unknown_coefficients = set(coefficients) - allowed_coefficients
    if unknown_coefficients:
        raise ValidationError(
            f"generation_water_l_per_kwh 含未知电源：{', '.join(sorted(unknown_coefficients))}"
        )
    for name, value in coefficients.items():
        _nonnegative(f"generation_water_l_per_kwh.{name}", value)
    return {
        "basis": basis, "limits_m3_h": limits, "Q_max_m3_h": min(limits.values()),
        "wue_l_per_kwh_it": wue,
        "generation_water_l_per_kwh": coefficients,
        "omitted": [key for key in ("source", "stress", "policy") if key not in limits],
    }


def land_capacity(land):
    """权威稿土地式：P_land=(A_eff-A_0)/a_site。"""
    allowed = {"effective_ha", "fixed_it_ha", "ha_per_mw_it"}
    if unknown := set(land) - allowed:
        raise ValidationError(f"land 含权威稿未使用字段：{', '.join(sorted(unknown))}")
    area = land.get("effective_ha")
    fixed = land.get("fixed_it_ha", 0)
    intensity = land.get("ha_per_mw_it")
    _nonnegative("effective_ha", area)
    _nonnegative("fixed_it_ha", fixed)
    _positive("ha_per_mw_it", intensity)
    return {
        "site_ha": area,
        "fixed_it_ha": fixed, "optimistic_zero_fixed": fixed == 0,
        "P_L_mw_it": max(0.0, area - fixed) / intensity,
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
    kind_value = spec.get("type")
    if not isinstance(kind_value, str):
        raise ValidationError("每套配置需要 type。")
    for field in ("C_PCC_mw", "generation_share"):
        if field in spec:
            raise ValidationError(f"权威稿 Q1 不使用字段 {field}，请删除后重算。")
    kind = kind_value.strip().lower()
    if kind not in Q1_TYPES:
        raise ValidationError(
            f"正稿 Q1 不包含方案类型 {kind}；可用类型为 {', '.join(sorted(Q1_TYPES))}。"
        )
    if kind == "wind" and grid > 0 and "alpha" in spec:
        raise ValidationError("并网风电需同期 net_output_mw 或 power_ratios 进行逐时平衡。")
    multiplier = spec.get("k_factor", data.get("k_factor"))
    row = _build_scenario(kind, spec, grid, multiplier, spec["name"])
    breakdown = row["breakdown"]
    electric, facility = total_capacity(grid, breakdown["self_generation_mw"], multiplier)
    breakdown.update(it_mw=electric, facility_mw=facility)
    if kind == "wind":
        row["method"]["capacity_basis"] = "恒定可交付电网与风电的逐时平衡" if grid else "孤立恒载最低出力"

    wue = spec.get("wue_l_per_kwh_it", budget["wue_l_per_kwh_it"])
    _nonnegative("wue_l_per_kwh_it", wue)
    generation_water_coefficient = spec.get(
        "generation_water_l_per_kwh",
        budget["generation_water_l_per_kwh"].get(kind, 0.0),
    )
    _nonnegative("generation_water_l_per_kwh", generation_water_coefficient)
    generation_water = breakdown["self_generation_mw"] * generation_water_coefficient
    net_water = max(0.0, budget["Q_max_m3_h"] - generation_water)
    water_limit = net_water / wue if wue > 0 else None
    land = land_capacity(data["land"])
    limits = {"电力": electric, "土地": land["P_L_mw_it"]}
    if water_limit is not None:
        limits["水"] = water_limit
    capacity = min(limits.values())
    row.update(name=spec["name"], online_year=spec["online_year"], land=land,
               wue_l_per_kwh_it=wue, P_E_mw_it=electric, P_W_mw_it=water_limit,
               generation_water_m3_h=generation_water, Q_net_m3_h=net_water,
               P_L_mw_it=land["P_L_mw_it"], P_mw_it=capacity,
               binding=[key for key, value in limits.items() if isclose(value, capacity, abs_tol=1e-9)])
    return row


def assess_site(data):
    for field in ("C_PCC_mw", "sensitivity"):
        if field in data:
            raise ValidationError(f"权威稿 Q1 不使用字段 {field}，请删除后重算。")
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
        rows.append(_resource_row(data, spec, grid, budget))
    if not rows:
        raise ValidationError(f"{year} 年没有满足投运条件的候选配置。")
    best = max(row["P_mw_it"] for row in rows)
    return {
        "site": data["site"], "assessment_year": year, "period_note": data["period_note"],
        "inputs": dict(data),
        "service_level": data["service_level"], "grid_basis": grid_basis, "water": budget,
        "scenarios": rows, "excluded": excluded, "P_max_mw_it": best,
        "winners": [row["name"] for row in rows if isclose(row["P_mw_it"], best, abs_tol=1e-9)],
    }
