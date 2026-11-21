import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from immc_power_capacity.app import run
from immc_power_capacity.core import ValidationError, assess_site, land_capacity, water_budget


@pytest.fixture
def site():
    return yaml.safe_load((ROOT / "examples/q1_site.yaml").read_text(encoding="utf-8"))


def test_demo_and_sensitivity(tmp_path):
    output = tmp_path / "result.json"
    report = run(ROOT / "examples/q1_site.yaml", output)
    assert json.loads(output.read_text(encoding="utf-8")) == report
    assert report["P_max_mw_it"] == 110
    assert report["winners"] == ["燃气配干冷园区"]
    assert report["excluded"][0]["online_year"] == 2030
    assert [row["binding"] for row in report["scenarios"]] == [["电力"], ["电力"], ["水"], ["土地"]]
    assert report["scenarios"][-1]["breakdown"]["facility_mw"] == 156
    assert report["water"]["limits_m3_h"] == {"source": 400, "stress": 150, "policy": 180}
    assert len(report["sensitivity"]) == 12
    upgraded = next(case for case in report["sensitivity"]
                    if case["parameter"] == "P_grid_mw" and case["value"] == 120)
    assert upgraded["scenarios"][0]["P_mw_it"] == 100
    assert upgraded["scenarios"][0]["binding"] == ["电力", "水"]


def test_minimal_config_defaults_generation_share():
    data = yaml.safe_load((ROOT / "examples/q1_minimal.yaml").read_text(encoding="utf-8"))
    report = assess_site(data)
    assert report["P_max_mw_it"] == 100
    assert report["scenarios"][0]["P_W_mw_it"] == 120
    assert report["scenarios"][0]["P_L_mw_it"] == 160
    assert report["scenarios"][0]["land"]["reserved_generation_ha"] == 0


def test_grid_conversion_and_tied_winners(site):
    del site["P_grid_mw"]
    site.update(P_grid_mva=120, power_factor=0.9)
    original = site["scenarios"][0]
    site["scenarios"] = [original, dict(original, name="第二接入方案")]
    report = assess_site(site)
    assert report["P_max_mw_it"] == 90
    assert len(report["winners"]) == 2
    assert "初筛" in report["grid_basis"]


def test_isolated_and_grid_wind(site):
    site["P_grid_mw"] = 0
    wind = dict(type="wind", name="风电", online_year=2028, alpha=0.2, installed_mw=120)
    site["scenarios"] = [wind]
    assert assess_site(site)["P_max_mw_it"] == 20
    site["P_grid_mw"] = 108
    with pytest.raises(ValidationError, match="同期"):
        assess_site(site)
    del wind["alpha"]
    wind["net_output_mw"] = [24, 12]
    assert assess_site(site)["scenarios"][0]["P_E_mw_it"] == 100


def test_land_and_year(site):
    site["assessment_year"] = 2025
    with pytest.raises(ValidationError, match="没有"):
        assess_site(site)
    assert land_capacity(dict(effective_ha=10, fixed_it_ha=10, ha_per_mw_it=1), 0)["P_L_mw_it"] == 0


def test_q1_rejects_combined_battery(site):
    site["scenarios"] = [{
        "name": "不在正稿内的方案",
        "type": "combined_battery",
        "online_year": 2028,
    }]
    with pytest.raises(ValidationError, match="正稿 Q1"):
        assess_site(site)


def test_period_budget_and_missing_limits(site):
    site["water"] = dict(basis="consumption", wue_l_per_kwh_it=2,
                         period_budget=dict(limit="policy", volume_m3=120, hours=2, it_load_factor=0.5))
    row = assess_site(site)["scenarios"][0]
    assert row["P_W_mw_it"] == 60
    assert water_budget(site["water"])["omitted"] == ["source", "stress"]
    site["water"].update(source_m3_h=90)
    assert assess_site(site)["scenarios"][0]["P_W_mw_it"] == 45
    site["water"]["wue_l_per_kwh_it"] = 0
    assert assess_site(site)["scenarios"][0]["P_mw_it"] == 90


@pytest.mark.parametrize("water", [
    {"basis": "withdrawal"},
    {"basis": "consumption", "river_m3_h": 1, "eco_m3_h": 0, "other_m3_h": 0},
    {"basis": "withdrawal", "source_m3_h": 1, "river_m3_h": 2, "eco_m3_h": 0, "other_m3_h": 0},
    {"basis": "withdrawal", "policy_m3_s": 1},
    {"basis": "withdrawal", "policy_m3_h": -1},
])
def test_invalid_or_ambiguous_water(water):
    with pytest.raises(ValidationError):
        water_budget(water)
