import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from .exceptions import InfeasibleError, ValidationError
from .validators import _efficiency, _nonnegative, _positive


def solve_storage_capacity(supply, dt, charge_max, discharge_max, usable_energy,
                           charge_efficiency, discharge_efficiency):
    """按附录 A 求整周期可维持的最大恒定附加负荷.

    决策变量顺序为 L, c_t, d_t, e_t, s_t, y_t。
    y_t=1 允许充电，y_t=0 允许放电；s_t 为非负弃电功率。
    """
    supply = _series(supply)
    _positive("dt_hours", dt)
    _nonnegative("C_max", charge_max)
    _nonnegative("D_max", discharge_max)
    _nonnegative("E_usable", usable_energy)
    _efficiency("charge_efficiency", charge_efficiency)
    _efficiency("discharge_efficiency", discharge_efficiency)
    if supply.size == 0:
        raise ValidationError("光储供电序列不能为空。")

    if charge_max == 0 and discharge_max == 0:
        return float(supply.min()), _schedule_without_battery(supply)

    periods = supply.size
    charge = slice(1, 1 + periods)
    discharge = slice(1 + periods, 1 + 2 * periods)
    energy = slice(1 + 2 * periods, 1 + 3 * periods)
    curtail = slice(1 + 3 * periods, 1 + 4 * periods)
    direction = slice(1 + 4 * periods, 1 + 5 * periods)
    variables = 1 + 5 * periods

    power_rows = np.zeros((periods, variables))
    energy_rows = np.zeros((periods, variables))
    for index in range(periods):
        power_rows[index, 0] = -1.0
        power_rows[index, 1 + index] = -1.0
        power_rows[index, 1 + periods + index] = 1.0
        power_rows[index, 1 + 3 * periods + index] = -1.0

        energy_rows[index, 1 + 2 * periods + index] -= 1.0
        energy_rows[index, 1 + 2 * periods + (index + 1) % periods] += 1.0
        energy_rows[index, 1 + index] -= charge_efficiency * dt
        energy_rows[index, 1 + periods + index] += dt / discharge_efficiency

    equality_matrix = np.vstack([power_rows, energy_rows])
    equality_lower = np.concatenate([-supply, np.zeros(periods)])
    equality_upper = equality_lower.copy()

    direction_rows = np.zeros((2 * periods, variables))
    direction_upper = np.zeros(2 * periods)
    for index in range(periods):
        direction_rows[index, 1 + index] = 1.0
        direction_rows[index, 1 + 4 * periods + index] = -charge_max
        direction_rows[periods + index, 1 + periods + index] = 1.0
        direction_rows[periods + index, 1 + 4 * periods + index] = discharge_max
        direction_upper[periods + index] = discharge_max
    direction_lower = np.full(2 * periods, -np.inf)

    matrix = np.vstack([equality_matrix, direction_rows])
    lower = np.concatenate([equality_lower, direction_lower])
    upper = np.concatenate([equality_upper, direction_upper])

    objective = np.zeros(variables)
    objective[0] = -1.0

    max_supply_result = milp(
        c=objective,
        constraints=LinearConstraint(matrix, lower, upper),
        bounds=Bounds(
            np.zeros(variables),
            np.concatenate([
                [np.inf],
                np.full(periods, charge_max),
                np.full(periods, discharge_max),
                np.full(periods, usable_energy),
                np.full(periods, np.inf),
                np.ones(periods),
            ]),
        ),
        integrality=np.concatenate([
            np.zeros(1 + 4 * periods, dtype=int),
            np.ones(periods, dtype=int),
        ]),
    )
    if not max_supply_result.success:
        raise InfeasibleError(f"附录 A 光储模型不可行：{max_supply_result.message}")

    optimal_load = float(max_supply_result.x[0])
    dispatch_objective = np.zeros(variables)
    dispatch_objective[energy.start] = 1.0
    dispatch_objective[curtail] = 1e-9
    dispatch_lower = np.zeros(variables)
    dispatch_lower[0] = optimal_load
    dispatch_upper = np.concatenate([
        [optimal_load],
        np.full(periods, charge_max),
        np.full(periods, discharge_max),
        np.full(periods, usable_energy),
        np.full(periods, np.inf),
        np.ones(periods),
    ])
    result = milp(
        c=dispatch_objective,
        constraints=LinearConstraint(matrix, lower, upper),
        bounds=Bounds(dispatch_lower, dispatch_upper),
        integrality=np.concatenate([
            np.zeros(1 + 4 * periods, dtype=int),
            np.ones(periods, dtype=int),
        ]),
    )
    if not result.success:
        raise InfeasibleError(f"附录 A 光储调度重建失败：{result.message}")

    solution = result.x
    schedule = {
        "L_mw": float(solution[0]),
        "charge_mw": solution[charge].tolist(),
        "discharge_mw": solution[discharge].tolist(),
        "energy_start_mwh": solution[energy].tolist(),
        "curtailment_mw": solution[curtail].tolist(),
        "direction": solution[direction].round().astype(int).tolist(),
        "status": result.message,
    }
    return optimal_load, schedule


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
