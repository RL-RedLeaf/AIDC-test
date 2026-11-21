"""IMMC 2027 A 题第一问：电、水、土地容量模型."""

from .app import calculate
from .core import (
    combined_battery,
    grid_only,
    hydro,
    solar,
    solve_storage_capacity,
    thermal,
    total_capacity,
    wind,
)

__all__ = [
    "calculate",
    "combined_battery",
    "grid_only",
    "hydro",
    "solar",
    "thermal",
    "wind",
    "total_capacity",
    "solve_storage_capacity",
]
