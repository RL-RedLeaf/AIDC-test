import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run as run_module
from immc_power_capacity.interactive import run_interactive


def _site_config():
    return yaml.safe_load((ROOT / "examples/q1_site.yaml").read_text(encoding="utf-8"))


def test_run_module_accepts_config_mapping(tmp_path):
    output = tmp_path / "function_result.json"
    report = run_module.calculate(_site_config(), output)
    assert report["P_max_mw_it"] == 110
    assert output.exists()


def test_interactive_wizard_collects_joint_configuration():
    answers = iter([
        "", "", "", "",  # 场址、年份、设计期、服务水平
        "1", "108", "", "",  # 电网 MW、PCC 留空、k
        "2", "1.5", "", "", "180",  # 取水口径、WUE、水量上限
        "", "", "", "",  # 土地四项
        "1", "", "", "", "",  # 纯电网方案
        "", "",  # 不继续添加、不写 JSON
    ])
    messages = []

    code = run_interactive(
        asker=lambda prompt: next(answers),
        say=lambda message="": messages.append(message),
    )

    assert code == 0, messages
    assert any("P_max = 90" in message for message in messages)
