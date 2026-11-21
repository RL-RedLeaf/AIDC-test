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
    """校验输入是否为有限实数。

    参数:
        field: 错误信息中显示的字段名。
        value: 待校验值。

    异常:
        ValidationError: 输入不是数值或包含无穷大、NaN。
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError(f"{field} 必须是数值。")
    if not math.isfinite(value):
        raise ValidationError(f"{field} 必须是有限数值。")


def _positive(field, value):
    """校验输入是否为有限正数。"""
    _finite_number(field, value)
    if value <= 0:
        raise ValidationError(f"{field} 必须为正数。")


def _nonnegative(field, value):
    """校验输入是否为有限非负数。"""
    _finite_number(field, value)
    if value < 0:
        raise ValidationError(f"{field} 不能为负。")


def _ratio(field, value):
    """校验输入是否位于闭区间 [0, 1]。"""
    _nonnegative(field, value)
    if value > 1:
        raise ValidationError(f"{field} 必须位于 [0, 1]。")


def _efficiency(field, value):
    """校验效率或功率因数是否位于半开区间 (0, 1]。"""
    _finite_number(field, value)
    if not (0 < value <= 1):
        raise ValidationError(f"{field} 必须位于 (0, 1]。")


def _positive_integer(field, value):
    """校验输入是否为正整数，例如机组台数或年份。"""
    _finite_number(field, value)
    if value <= 0 or not float(value).is_integer():
        raise ValidationError(f"{field} 必须是正整数。")


def _k_factor(value):
    """校验满载设施倍率；权威稿要求 k >= 1。"""
    _finite_number("k_factor", value)
    if value < 1:
        raise ValidationError("k_factor 不能小于 1。")


def _finite_nonnegative(values, field):
    """校验一维时间序列，要求非空、有限且各元素非负。"""
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
    """计算园区总功率和额定 IT 容量。

    对应权威稿式 (1)、(6):
        P_total = P_grid + P_self
        P_E = P_total / k

    参数:
        grid_mw: 接入点可持续交付的电网净有功，MW。
        self_generation_mw: 自建电源可靠净增量，MW。
        k_factor: 设计满载设施总功率与同一工况 IT 功率之比。

    返回:
        (P_E, P_total)，分别为 MW IT 和 MW。
    """
    _nonnegative("P_grid", grid_mw)
    _nonnegative("P_self", self_generation_mw)
    _k_factor(k_factor)
    facility_mw = grid_mw + self_generation_mw
    return facility_mw / k_factor, facility_mw


def _storage_series(values):
    """将逐时可用净功率转换为校验过的一维 NumPy 数组。"""
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
    """生成无电池时段的调度记录。

    无电池时，恒定附加负荷受最弱时段净功率限制；
    其余发电量全部记为弃电。
    """
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
    """求光储系统在整个周期内可维持的最大恒定附加负荷。

    该函数实现权威稿附录 A:
        r_t + d_t >= L + c_t
        e_(t+1) = e_t + eta_c*c_t*dt - d_t*dt/eta_d
        0 <= c_t <= C_max
        0 <= d_t <= D_max
        0 <= e_t <= E_usable
        e_(T+1) = e_1

    参数:
        supply: 各时段自建电源可用净功率 r_t，MW。
        dt: 时段长度，h。
        charge_max: 最大充电功率 C_max，MW。
        discharge_max: 最大放电功率 D_max，MW。
        usable_energy: 可用电量 E_usable，MWh。
        charge_efficiency: 充电效率 eta_c。
        discharge_efficiency: 放电效率 eta_d。

    返回:
        (L, schedule)。L 为 MW；schedule 包含充放电、荷电量、
        弃电量、方向和求解状态。

    说明:
        先求最大 L，再固定 L 最小化期初电量。第二次求解后用净入库
        电量重建单方向调度，避免同一时段同时充放电。
    """
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
    # 使用稀疏矩阵构造 LP，避免时段数很大时生成稠密矩阵。
    identity = eye(periods, format="csr")
    indices = np.arange(periods)
    successor = csr_matrix((np.ones(periods), (indices, (indices + 1) % periods)),
                           shape=(periods, periods))
    zero_column = csr_matrix((periods, 1))
    # 功率约束：L + c_t - d_t <= r_t。
    power = hstack(
        [np.ones((periods, 1)), identity, -identity, csr_matrix(identity.shape)],
        format="csr",
    )
    # 电量平衡：e_(t+1) - e_t - eta_c*c_t*dt + d_t*dt/eta_d = 0。
    energy_balance = hstack(
        [
            zero_column,
            -dt * charge_efficiency * identity,
            dt / discharge_efficiency * identity,
            successor - identity,
        ],
        format="csr",
    )
    bounds = ([(0, None)] + [(0, charge_max)] * periods + [(0, discharge_max)] * periods
              + [(0, usable_energy)] * periods)
    # 第一次目标：最大化 L。
    objective = np.zeros(1 + 3 * periods)
    objective[0] = -1
    constraints = dict(A_ub=power, b_ub=supply, A_eq=energy_balance, b_eq=np.zeros(periods),
                       method="highs")
    result = linprog(objective, bounds=bounds, **constraints)
    if not result.success:
        raise InfeasibleError(f"光储容量求解失败：{result.message}")

    # 第二次目标：固定 L，最小化期初电量，得到唯一性更好的调度。
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
    """计算纯电网基准方案。

    纯电网方案取 P_self=0，对应权威稿式 (1)、(6) 的退化情况。
    """
    _nonnegative("P_grid", grid_mw)
    _k_factor(k_factor)
    return _breakdown(grid_mw, 0.0, k_factor, "grid_only", {
        "equation": "正文式(1)、(6)",
        "assumption": "P_self = 0，作为所有候选方案的基准。",
    })


def thermal(name, grid_mw, k_factor, units, unit_net_mw,
            net_efficiency=None, gas_supply_adequate=None):
    """计算煤电或燃气的可靠容量。

    对应权威稿式 (2)：
        P_j = N_j * p_j^net
    其中 units=N_j，unit_net_mw=p_j^net，单位均为 MW。
    net_efficiency 只用于报告燃料热功率，不改变净电容量。
    """
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

    # 煤电、燃气均为可同时运行机组台数乘以单机持续净功率。
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
    """计算风电的可靠容量。

    对应权威稿式 (3)：
        X_wind = A_wind * rho_wind
        P_wind = alpha_wind * X_wind

    alpha 可以由输入直接给出，也可以由逐时净功率序列取
    min(net_output_mw) / X_wind 得到。并网场景应提供同期序列。

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
    # alpha_wind 是考察期最低净出力与装机之比，不是年度容量因子。
    capacity = installed_mw * alpha_value
    return _breakdown(grid_mw, capacity, k_factor, "wind", {
        "equation": "正文式(3)",
        "installed_mw": installed_mw,
        "alpha": alpha_value,
        "alpha_source": source,
    })


def hydro(name, grid_mw, k_factor, installed_mw, flow_m3_per_s, net_head_m, efficiency):
    """计算园区专用水电的可靠容量。

    对应权威稿式 (4)：
        P_hydro = min(X_hydro, 0.00981*eta_hydro*Q*H)
    流量 Q 与落差 H 必须采用同一约束期口径。
    """
    _nonnegative("P_grid", grid_mw)
    _k_factor(k_factor)
    _nonnegative("installed_mw", installed_mw)
    _nonnegative("flow_m3_per_s", flow_m3_per_s)
    _nonnegative("net_head_m", net_head_m)
    _efficiency("hydraulic_efficiency", efficiency)
    # 0.00981 将 rho*g*Q*H 换算为 MW。
    water_power = 0.00981 * efficiency * flow_m3_per_s * net_head_m
    capacity = min(installed_mw, water_power)
    return _breakdown(grid_mw, capacity, k_factor, "hydro", {
        "equation": "正文式(4)",
        "installed_mw": installed_mw,
        "water_power_mw": water_power,
    })


def solar(name, grid_mw, k_factor, area_km2, density_mw_per_km2,
          supply_ratios=None, dt_hours=None, battery=None, net_output_mw=None):
    """计算无电池光伏或光储的可靠容量。

    对应权威稿式 (5)：
        X_PV = A_PV * rho_PV
        P_PV+st = f_PV+st(X_PV, W, Cmax, Dmax, Eusable, eta_c, eta_d)

    supply_ratios 的单位为 MWh/MWh，net_output_mw 为 MW。
    无电池时退化为考察期最小净功率；有电池时调用附录 A 的 LP。

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
    # 电池调度只使用光伏可用净功率，不把电网功率用于给电池充电。
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
    """计算风电与光伏共用电池的可靠容量。

    先按同一时段合并风光净功率 r_t，再对合并后的序列求解一次
    附录 A。installed_mw 是风光合计装机，仅用于记录配置。
    """
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
    """解析并校验电池容量、功率和效率参数。"""
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
    """构造统一的方案结果字典。

    返回的 breakdown 字段与终端/JSON 输出保持一致，便于逐方案复核。
    """
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
    """从方案配置读取一维序列，支持内嵌数组或 module::variable。"""
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
    """从方案配置读取并校验一个数值字段。"""
    if field not in spec or spec[field] is None:
        raise CapacityModelError(f"{field} 不能缺失。")
    value = spec[field]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise CapacityModelError(f"{field} 必须是数值。")
    return value


def _config_optional(spec, field):
    """读取可选数值字段；缺失或为 null 时返回 None。"""
    return None if field not in spec or spec[field] is None else _config_number(spec, field)


def _build_scenario(kind, spec, grid_value, k_value, name):
    """按方案类型分派到对应的电源计算函数。

    这是输入配置与电源公式之间的适配层，不改变任何物理计算。
    """
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
    """从方案配置提取风电参数并调用 wind()。"""
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
    """从方案配置提取光伏/光储参数并调用 solar()。"""
    provided = [
        field for field in ("supply_ratios", "net_output_mw")
        if spec.get(field) is not None
    ]
    if len(provided) != 1:
        raise CapacityModelError("光伏方案必须在 supply_ratios 与 net_output_mw 中提供且只提供一个。")
    source = provided[0]
    return solar(
        "solar",
        grid_value,
        k_value,
        _config_number(spec, "area_km2"),
        _config_number(spec, "density_mw_per_km2"),
        supply_ratios=(
            _config_series(spec, source, required=True)
            if source == "supply_ratios"
            else None
        ),
        net_output_mw=(
            _config_series(spec, source, required=True)
            if source == "net_output_mw"
            else None
        ),
        dt_hours=_config_number(spec, "dt_hours"),
        battery=spec.get("battery"),
    )


Q1_TYPES = frozenset({"grid", "coal", "gas", "wind", "hydro", "solar", "combined_battery"})


def _resolve_wue(water):
    """解析 WUE，支持直接值或夏冬时段加权值。"""
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
    """计算场址的最终可用水量上限。

    参数:
        water: YAML 中的 water 对象。流量统一为 m³/h，
            WUE 为 L/kWh IT。

    返回:
        包含各项水量上限、Q_max、WUE、发电耗水系数和 omitted 的字典。

    说明:
        三项水量上限只有一项是必需的实际限制；未提供的项会列入
        ``omitted``，不会被自动视为无穷大。
    """
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


def land_capacity(land, generation_land=None):
    """计算园区土地允许的最大 IT 容量。

    对应权威稿 Q1-v2 土地模型:
        A_req = A_0 + A_e + a_site * P
        P_land = max(0, (A_eff - A_0 - A_e) / a_site)

    参数:
        land: 含 effective_ha、fixed_it_ha、generation_land_ha、
            ha_per_mw_it 的字典。
        generation_land: 可选的方案级 A_e 覆盖值；缺省使用 land 中的值。
    """
    allowed = {
        "effective_ha",
        "fixed_it_ha",
        "generation_land_ha",
        "generation_land_options_ha",
        "ha_per_mw_it",
    }
    if unknown := set(land) - allowed:
        raise ValidationError(f"land 含权威稿未使用字段：{', '.join(sorted(unknown))}")
    area = land.get("effective_ha")
    fixed = land.get("fixed_it_ha", 0)
    if generation_land is None:
        generation_land = land.get("generation_land_ha", 0)
    intensity = land.get("ha_per_mw_it")
    _nonnegative("effective_ha", area)
    _nonnegative("fixed_it_ha", fixed)
    _nonnegative("generation_land_ha", generation_land)
    _positive("ha_per_mw_it", intensity)
    return {
        "site_ha": area,
        "fixed_it_ha": fixed,
        "generation_land_ha": generation_land,
        "optimistic_zero_fixed": fixed == 0,
        "P_L_mw_it": max(0.0, area - fixed - generation_land) / intensity,
    }


def _generation_land_options(land, spec):
    """解析 A_e 的固定值或候选值列表。

    返回:
        (候选值列表, 来源)。来源为 ``fixed``、``options`` 或 ``default``。
    """
    spec_fixed = spec.get("generation_land_ha")
    spec_options = spec.get("generation_land_options_ha")
    land_fixed = land.get("generation_land_ha")
    land_options = land.get("generation_land_options_ha")
    fixed = spec_fixed if spec_fixed is not None else (
        None if spec_options is not None else land_fixed
    )
    options = spec_options if spec_options is not None else (
        None if spec_fixed is not None else land_options
    )
    if fixed is not None and options is not None:
        raise ValidationError(
            "generation_land_ha 与 generation_land_options_ha 不能同时提供。"
        )
    if fixed is not None:
        _nonnegative("generation_land_ha", fixed)
        return [fixed], "fixed"
    if options is not None:
        if not isinstance(options, (list, tuple)) or not options:
            raise ValidationError("generation_land_options_ha 必须是非空列表。")
        values = []
        for value in options:
            _nonnegative("generation_land_options_ha", value)
            values.append(value)
        return values, "options"
    return [0.0], "default"


def _generation_area_km2(kind, spec):
    """返回风电或光伏的资源面积，单位为 km²。

    光伏必须显式提供 ``area_km2``；风电可以显式提供面积，也可以用
    ``installed_mw / density_mw_per_km2`` 反推。无法确定面积时返回
    ``None``，此时只能依赖 ``generation_land_required_ha`` 显式约束。
    """
    if kind not in {"wind", "solar"}:
        return None
    area = spec.get("area_km2")
    if area is not None:
        _nonnegative("area_km2", area)
        return float(area)
    if kind == "wind":
        installed = spec.get("installed_mw")
        density = spec.get("density_mw_per_km2")
        if installed is not None and density is not None:
            _nonnegative("installed_mw", installed)
            _positive("density_mw_per_km2", density)
            return float(installed) / density
    return None


def _generation_land_required(kind, spec):
    """估算方案自身的发电设施用地 A_gen。

    水电占地按要求忽略；火电需要 ``unit_land_ha``，风光用合格面积
    换算，combined_battery 可用 ``generation_land_required_ha`` 显式给出。
    """
    explicit = spec.get("generation_land_required_ha")
    if explicit is not None:
        _nonnegative("generation_land_required_ha", explicit)
        return explicit
    if kind in {"coal", "gas"}:
        unit_land = spec.get("unit_land_ha")
        if unit_land is None:
            return 0.0
        _nonnegative("unit_land_ha", unit_land)
        units = spec.get("units", 0)
        _nonnegative("units", units)
        return units * unit_land
    if kind in {"wind", "solar"}:
        area = _generation_area_km2(kind, spec)
        return 0.0 if area is None else area * 100.0
    return 0.0


def _cap_generation_by_land(kind, spec, generation_land):
    """按 A_e 限制方案可用的发电设备规模。

    火电按单机用地向下取整；风电和光伏按可用面积缩放。水电占地
    不纳入，容量保持不变。返回 ``None`` 表示该候选 A_e 连一个
    可用机组或最小资源面积都无法容纳。
    """
    limited = dict(spec)
    if spec.get("generation_land_in_site", True) is False:
        return limited, _generation_land_required(kind, spec), False
    explicit = spec.get("generation_land_required_ha")
    if explicit is not None:
        _nonnegative("generation_land_required_ha", explicit)
        if explicit > generation_land + 1e-9:
            return None
        return limited, explicit, False
    if kind in {"coal", "gas"} and spec.get("unit_land_ha") is not None:
        unit_land = spec["unit_land_ha"]
        _nonnegative("unit_land_ha", unit_land)
        if unit_land > 0:
            requested_units = int(spec.get("units", 0))
            max_units = int((generation_land + 1e-9) // unit_land)
            if max_units < 1:
                return None
            limited["units"] = min(requested_units, max_units)
            required = limited["units"] * unit_land
            return limited, required, limited["units"] != requested_units
    if kind in {"wind", "solar"}:
        area = _generation_area_km2(kind, spec)
        if area is not None:
            available_area = generation_land / 100.0
            if available_area <= 0:
                return None
            if area <= 0:
                return limited, 0.0, False
            effective_area = min(area, available_area)
            ratio = effective_area / area
            limited["area_km2"] = effective_area
            if spec.get("installed_mw") is not None:
                limited["installed_mw"] = spec["installed_mw"] * ratio
            if isinstance(spec.get("net_output_mw"), (list, tuple)):
                limited["net_output_mw"] = [
                    value * ratio for value in spec["net_output_mw"]
                ]
            required = effective_area * 100.0
            return limited, required, effective_area != area
    required = spec.get("generation_land_required_ha", 0.0)
    _nonnegative("generation_land_required_ha", required)
    if required > generation_land + 1e-9:
        return None
    return limited, required, False


def _grid(data):
    """解析电网输入，返回 P_grid 及其口径说明。

    MW 输入直接使用；MVA 输入按 S_grid*cos(phi) 换算，并标注为
    初筛上界。两项不能同时提供。
    """
    if ("P_grid_mw" in data) == ("P_grid_mva" in data):
        raise ValidationError("电网需给 P_grid_mw 或 P_grid_mva 中的一项。")
    if "P_grid_mva" in data:
        _nonnegative("P_grid_mva", data["P_grid_mva"])
        _efficiency("power_factor", data.get("power_factor"))
        return data["P_grid_mva"] * data["power_factor"], "MVA × 功率因数，初筛上界"
    _nonnegative("P_grid_mw", data["P_grid_mw"])
    return data["P_grid_mw"], "接入点持续净有功"


def _resource_row_single(data, spec, grid, budget):
    """计算单个候选方案的三类上限和联合容量。

    这里是 Q1 的逐方案集成点：
        P_E = total_capacity(...)
        P_W = max(0, Q_max - Q_gen) / WUE
        P_L = land_capacity(...)
        P = min(P_E, P_W, P_L)

    ``binding`` 记录达到最小值的约束；并列时保留多个名称。
    """
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
    # P_i 用 MW、c_i 用 L/kWh 时，乘积数值直接对应 m³/h。
    generation_water = breakdown["self_generation_mw"] * generation_water_coefficient
    net_water = max(0.0, budget["Q_max_m3_h"] - generation_water)
    water_limit = net_water / wue if wue > 0 else None
    value_source = {"P_E": "derived", "P_W": "derived", "P_L": "derived"}
    direct_power = spec.get("direct_P_E_mw_it")
    if direct_power is not None:
        _nonnegative("direct_P_E_mw_it", direct_power)
        electric = direct_power
        breakdown["it_mw"] = electric
        breakdown["value_source"] = "direct"
        value_source["P_E"] = "direct"
    direct_water = spec.get("direct_P_W_mw_it")
    if direct_water is not None:
        _nonnegative("direct_P_W_mw_it", direct_water)
        water_limit = direct_water
        value_source["P_W"] = "direct"

    direct_land = spec.get("direct_P_L_mw_it")
    required_generation_land = _generation_land_required(kind, spec)
    if spec.get("generation_land_in_site", True) is False:
        land_options, land_source = [0.0], "external"
        site_land_required = 0.0
    else:
        land_options, land_source = _generation_land_options(data["land"], spec)
        site_land_required = required_generation_land
    feasible_land_options = [
        value
        for value in land_options
        if value + 1e-9 >= site_land_required
    ]
    if not feasible_land_options:
        raise ValidationError(
            f"{spec['name']} 的自建发电站用地不足：需要 {site_land_required:g} ha，"
            f"候选只有 {', '.join(f'{value:g}' for value in land_options)} ha。"
        )
    land_options = feasible_land_options
    land_candidates = []
    selected = None
    for generation_land in land_options:
        candidate_land = land_capacity(data["land"], generation_land)
        candidate_limits = {"电力": electric, "土地": candidate_land["P_L_mw_it"]}
        if water_limit is not None:
            candidate_limits["水"] = water_limit
        candidate_capacity = min(candidate_limits.values())
        candidate_binding = [
            key
            for key, value in candidate_limits.items()
            if isclose(value, candidate_capacity, abs_tol=1e-9)
        ]
        candidate = {
            "generation_land_ha": generation_land,
            "P_L_mw_it": candidate_land["P_L_mw_it"],
            "P_mw_it": candidate_capacity,
            "binding": candidate_binding,
        }
        land_candidates.append(candidate)
        if selected is None or (
            candidate_capacity,
            -generation_land,
        ) > (
            selected["P_mw_it"],
            -selected["generation_land_ha"],
        ):
            selected = candidate

    land = land_capacity(data["land"], selected["generation_land_ha"])
    if direct_land is not None:
        _nonnegative("direct_P_L_mw_it", direct_land)
        land["P_L_mw_it"] = direct_land
        land["value_source"] = "direct"
        value_source["P_L"] = "direct"
        land_source = "direct"
        direct_limits = {"电力": electric, "土地": direct_land}
        if water_limit is not None:
            direct_limits["水"] = water_limit
        direct_capacity = min(direct_limits.values())
        land_candidates = [{
            "generation_land_ha": land["generation_land_ha"],
            "P_L_mw_it": direct_land,
            "P_mw_it": direct_capacity,
            "binding": [
                key
                for key, value in direct_limits.items()
                if isclose(value, direct_capacity, abs_tol=1e-9)
            ],
        }]
        selected = land_candidates[0]
    elif land_source == "options":
        value_source["P_L"] = "optimized"
    land["generation_land_source"] = land_source

    limits = {"电力": electric, "土地": land["P_L_mw_it"]}
    if water_limit is not None:
        limits["水"] = water_limit
    capacity = min(limits.values())
    if direct_land is not None:
        land_candidates[0]["binding"] = [
            key
            for key, value in limits.items()
            if isclose(value, capacity, abs_tol=1e-9)
        ]
        land_candidates[0]["P_mw_it"] = capacity
    row.update(
        name=spec["name"],
        online_year=spec["online_year"],
        land=land,
        wue_l_per_kwh_it=wue,
        P_E_mw_it=electric,
        P_W_mw_it=water_limit,
        generation_water_m3_h=generation_water,
        Q_net_m3_h=net_water,
        P_L_mw_it=land["P_L_mw_it"],
        P_mw_it=capacity,
        generation_land_ha=selected["generation_land_ha"],
        generation_land_source=land_source,
        generation_land_required_ha=required_generation_land,
        generation_land_candidates=land_candidates,
        value_source=value_source,
        binding=[
            key
            for key, value in limits.items()
            if isclose(value, capacity, abs_tol=1e-9)
        ],
    )
    return row


def _resource_row(data, spec, grid, budget):
    """在 A_e 候选上限制设备规模，并选择联合容量最大的方案。"""
    if spec.get("generation_land_in_site", True) is False:
        land_options, land_source = [0.0], "external"
    else:
        land_options, land_source = _generation_land_options(data["land"], spec)
    candidates = []
    for generation_land in land_options:
        capped = _cap_generation_by_land(spec["type"].strip().lower(), spec, generation_land)
        if capped is None:
            continue
        limited_spec, required_land, capacity_capped = capped
        limited_spec = dict(limited_spec)
        limited_spec["generation_land_ha"] = generation_land
        limited_spec.pop("generation_land_options_ha", None)
        row = _resource_row_single(data, limited_spec, grid, budget)
        row["generation_land_required_ha"] = required_land
        row["generation_land_capacity_capped"] = capacity_capped
        candidates.append(row)
    if not candidates:
        raise ValidationError(
            f"{spec['name']} 的 A_e 候选无法容纳配置的发电设备。"
        )

    selected = max(
        candidates,
        key=lambda row: (
            row["P_mw_it"],
            -row["generation_land_ha"],
        ),
    )
    selected["generation_land_source"] = (
        "direct"
        if selected["value_source"]["P_L"] == "direct"
        else land_source
    )
    if land_source == "options" and selected["value_source"]["P_L"] != "direct":
        selected["value_source"]["P_L"] = "optimized"
    selected["generation_land_candidates"] = [
        {
            "generation_land_ha": row["generation_land_ha"],
            "generation_land_required_ha": row["generation_land_required_ha"],
            "generation_land_capacity_capped": row[
                "generation_land_capacity_capped"
            ],
            "P_L_mw_it": row["P_L_mw_it"],
            "P_mw_it": row["P_mw_it"],
            "binding": row["binding"],
        }
        for row in candidates
    ]
    selected["land"]["generation_land_source"] = selected[
        "generation_land_source"
    ]
    return selected


def assess_site(data):
    """在单一给定场址上评估所有候选方案。

    处理顺序:
        1. 校验场址、水量和土地输入；
        2. 按 assessment_year 筛选已投运方案；未填 online_year 时按该年处理；
        3. 逐方案计算 P_E、P_W、P_L 和 P=min(...)；
        4. 取候选集最大值并记录 winners、binding 和 excluded。

    返回:
        可直接写入 JSON 的 Q1 结果字典。
    """
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
        if (
            not isinstance(spec, dict)
            or not isinstance(spec.get("name"), str)
            or not spec["name"].strip()
        ):
            raise ValidationError("每套配置需要 name。")
        if spec["name"] in names:
            raise ValidationError(f"配置名称重复：{spec['name']}")
        names.add(spec["name"])
        online_year = spec.get("online_year")
        if online_year is None:
            online_year = year
        else:
            _positive_integer("online_year", online_year)
        online_year = int(online_year)
        if online_year > year:
            excluded.append({
                "name": spec["name"],
                "online_year": online_year,
                "reason": "尚未投运",
            })
            continue
        normalized = dict(spec)
        normalized["online_year"] = online_year
        rows.append(_resource_row(data, normalized, grid, budget))
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
