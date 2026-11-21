"""两种评估入口共用的供电配置解析。"""

import importlib

from .calculator import combined_battery, grid_only, hydro, solar, thermal, wind
from .exceptions import CapacityModelError


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
