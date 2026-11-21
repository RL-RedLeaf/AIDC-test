import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from immc_power_capacity.cli import calculate, main, run
from immc_power_capacity.interactive import run_interactive

__all__ = ["calculate", "run", "run_interactive", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
