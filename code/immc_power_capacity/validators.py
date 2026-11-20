import math

import numpy as np

from .exceptions import ValidationError


def _number(field, value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError(f"{field} 必须是数值。")
    if not math.isfinite(value):
        raise ValidationError(f"{field} 必须是有限数值。")


def _positive(field, value):
    _number(field, value)
    if value <= 0:
        raise ValidationError(f"{field} 必须为正数。")


def _nonnegative(field, value):
    _number(field, value)
    if value < 0:
        raise ValidationError(f"{field} 不能为负。")


def _ratio(field, value):
    _nonnegative(field, value)
    if value > 1:
        raise ValidationError(f"{field} 必须位于 [0, 1]。")


def _efficiency(field, value):
    _number(field, value)
    if not (0 < value <= 1):
        raise ValidationError(f"{field} 必须位于 (0, 1]。")


def _positive_integer(field, value):
    _number(field, value)
    if value <= 0 or not float(value).is_integer():
        raise ValidationError(f"{field} 必须是正整数（机组台数）。")


def _k_factor(value):
    _number("k_factor", value)
    if value <= 1:
        raise ValidationError("k_factor 必须大于 1（必须扣除冷却和配电功率）。")


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
