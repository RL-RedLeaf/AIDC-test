from .exceptions import ValidationError


def total_capacity(grid_mw, self_generation_mw, k_factor):
    """按 v2 式(1)与(6)计算园区总功率与额定 IT 容量."""
    _number("P_grid", grid_mw)
    _number("P_self", self_generation_mw)
    _number("k_factor", k_factor)
    if grid_mw < 0:
        raise ValidationError("P_grid 不能为负。")
    if self_generation_mw < 0:
        raise ValidationError("P_self 不能为负。")
    if k_factor <= 1:
        raise ValidationError("k_factor 必须大于 1（必须扣除冷却和配电功率）。")
    facility_mw = grid_mw + self_generation_mw
    return facility_mw / k_factor, facility_mw


def _number(field, value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError(f"{field} 必须是数值。")
    if value != value or value in (float("inf"), float("-inf")):
        raise ValidationError(f"{field} 必须是有限数值。")
