"""IMMC 2027 A 题第一问：电、水、土地容量模型."""

from .calculator import combined_battery, grid_only, hydro, solar, thermal, wind
from .cli import calculate
from .model import total_capacity
from .solver import solve_storage_capacity

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
