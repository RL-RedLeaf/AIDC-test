import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, eye, hstack

from .exceptions import InfeasibleError, ValidationError
from .validators import _efficiency, _nonnegative, _positive


def solve_storage_capacity(supply, dt, charge_max, discharge_max, usable_energy,
                           charge_efficiency, discharge_efficiency):
    """用稀疏 LP 求周期恒载，再以相同的电量轨迹重建单方向调度。"""
    supply = _series(supply)
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


def _series(values):
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
