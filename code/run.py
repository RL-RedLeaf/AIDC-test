"""IMMC 2027 A 题 Q1 和 Q2 的脚本入口。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from immc_power_capacity.app import calculate, main, run, run_interactive

__all__ = ["calculate", "run", "run_interactive", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
