from .exceptions import ValidationError
from .model import total_capacity
from .solver import solve_storage_capacity
from .validators import (
    _efficiency,
    _finite_nonnegative,
    _k_factor,
    _nonnegative,
    _positive,
    _positive_integer,
    _ratio,
)


def grid_only(grid_mw, k_factor):
    """纯电网方案：P_self=0."""
    _nonnegative("P_grid", grid_mw)
    _k_factor(k_factor)
    return _breakdown(grid_mw, 0.0, k_factor, "grid_only", {
        "equation": "v2 式(1)(6)",
        "assumption": "P_self = 0，作为所有候选方案的基准。",
    })


def thermal(name, grid_mw, k_factor, units, unit_net_mw,
            net_efficiency=None, gas_supply_adequate=None):
    """煤电或燃气：可同时运行台数 × 单机持续净功率，v2 式(2)."""
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
        "equation": "v2 式(2)",
        "units": int(units),
        "unit_net_mw": unit_net_mw,
        "fuel_heat_needed_mw": (
            None if net_efficiency is None else self_generation / net_efficiency
        ),
        "gas_supply": gas_note,
    })


def wind(name, grid_mw, k_factor, area_km2=None, density_mw_per_km2=None,
         alpha=None, power_ratios=None, net_output_mw=None, installed_mw=None):
    """风电：v2 式(3).

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
        "equation": "v2 式(3)",
        "installed_mw": installed_mw,
        "alpha": alpha_value,
        "alpha_source": source,
    })


def hydro(name, grid_mw, k_factor, installed_mw, flow_m3_per_s, net_head_m, efficiency):
    """水电：v2 式(4)，流量与落差必须采用同一约束期口径."""
    _nonnegative("P_grid", grid_mw)
    _k_factor(k_factor)
    _nonnegative("installed_mw", installed_mw)
    _nonnegative("flow_m3_per_s", flow_m3_per_s)
    _nonnegative("net_head_m", net_head_m)
    _efficiency("hydraulic_efficiency", efficiency)
    water_power = 0.00981 * efficiency * flow_m3_per_s * net_head_m
    capacity = min(installed_mw, water_power)
    return _breakdown(grid_mw, capacity, k_factor, "hydro", {
        "equation": "v2 式(4)",
        "installed_mw": installed_mw,
        "water_power_mw": water_power,
    })


def solar(name, grid_mw, k_factor, area_km2, density_mw_per_km2,
          supply_ratios=None, dt_hours=None, battery=None, net_output_mw=None):
    """光伏无电池、光储或参与共用电池的逐时容量：v2 式(5)、附录 A.

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
            "equation": "v2 式(5)；附录 A" if has_battery else "v2 式(5) 无电池退化（周期最小净功率）",
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
        "equation": "v2 式(5)；附录 A（风光合并后一次求解）",
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
