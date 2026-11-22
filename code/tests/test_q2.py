import json
import math
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from immc_power_capacity.app import calculate, main
from immc_power_capacity.core import ValidationError


@pytest.fixture
def network():
    examples = ROOT / "examples"
    data = yaml.safe_load((examples / "q2_network.yaml").read_text(encoding="utf-8"))
    data["sites"]["中心"] = yaml.safe_load((examples / "q1_minimal.yaml").read_text(encoding="utf-8"))
    return data


def test_paired_loads_footprints_and_scores_from_cli(tmp_path):
    output = tmp_path / "result.json"
    assert main([str(ROOT / "examples/q2_network.yaml"), "--json", str(output)]) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    central = report["plans"]["centralized"]
    distributed = report["plans"]["distributed"]
    assert central["footprint"] == {"carbon_t_co2": 84, "water_m3": 210, "land_ha": 80}
    assert central["F"] == 0
    assert central["daily_average"] == {"carbon_kg_co2_per_day": 1008000, "water_kg_per_day": 2520000}
    assert central["omega"] == pytest.approx(0.65)
    assert distributed["footprint"] == {"carbon_t_co2": 85.5, "water_m3": 175, "land_ha": 98}
    assert distributed["wan_mwh"] == 3
    assert distributed["hotspots"] == {"water": ["西站", "东站"], "grid": ["西站"], "land": ["西站", "东站"]}
    expected_f = math.log(0.4 * 85.5 / 84 + 0.3 * 175 / 210 + 0.3 * 98 / 80)
    expected_s = 0.4 * 2 / 3 + 0.4 + 0.2 * 49 / 71
    assert distributed["omega"] == pytest.approx(expected_f + 0.25 * expected_s)
    assert report["winners"] == ["distributed"]


def test_same_total_over_period_does_not_mask_missed_hour(network):
    network["distributed"]["nodes"][0]["compute"] = [31, 39]
    with pytest.raises(ValidationError, match="第 1 时段分配的算力"):
        calculate(network)


def test_selected_capacity_and_actual_generation(network):
    site = network["sites"]["中心"]
    site.update(P_grid_mw=72, scenarios=site["scenarios"] + [
        {"type": "gas", "name": "燃机", "units": 1, "unit_net_mw": 32,
         "generation_water_l_per_kwh": 0.5},
        {"type": "gas", "name": "较大燃机", "units": 2, "unit_net_mw": 32}])
    node = network["centralized"]["nodes"][0]
    node.update(scenario="燃机", self_co2_t_per_mwh=0.8)
    row = calculate(network)["plans"]["centralized"]["nodes"][0]
    assert row["q1_capacity_mw_it"] == pytest.approx(104 / 1.2)
    assert [period["self_generation_mw"] for period in row["periods"]] == [0, 24]
    assert row["footprint"]["water_m3"] == 210 + 24 * 0.5
    assert row["footprint"]["carbon_t_co2"] == pytest.approx(144 * 0.5 + 24 * 0.8)
    node["installed_it_mw"] = 90
    report = calculate(network)
    assert not report["plans"]["centralized"]["feasible"]
    assert report["winners"] == ["distributed"]


def test_pressure_at_boundary_cannot_win(network):
    network["centralized"]["nodes"][0]["local_grid_available_mw"] = 96
    network["lambda"] = 0
    network["pressure_weights"] = {"grid": 0, "land": 1, "water": 0}
    report = calculate(network)
    central = report["plans"]["centralized"]
    assert central["pressure"]["grid"] == 1
    assert central["nodes"][0]["grid_remaining_fraction"] == 0
    assert central["S"] is central["omega"] is None
    assert report["winners"] == ["distributed"]
    network["distributed"]["nodes"][0]["local_water_available_m3_h"] = 0
    report = calculate(network)
    assert report["winners"] == []
    assert report["plans"]["distributed"]["hotspots"]["water"] == ["西站"]
    json.dumps(report, allow_nan=False)


def test_variable_solar_output_saves_daytime_grid_energy(network):
    site = network["sites"]["中心"]
    site["scenarios"] = [{"name": "光伏", "type": "solar", "area_km2": 1,
                          "density_mw_per_km2": 24, "dt_hours": 1, "net_output_mw": [24, 0],
                          "generation_land_in_site": False}]
    node = network["centralized"]["nodes"][0]
    node.update(scenario="光伏", self_generation_mw=[24, 0], self_co2_t_per_mwh=0)
    central = calculate(network)["plans"]["centralized"]
    assert central["feasible"]
    assert central["footprint"]["carbon_t_co2"] == 72
    assert central["footprint"]["land_ha"] == 180
    assert central["pressure"]["land"] == 0.5
    node["self_generation_mw"] = [0, 24]
    assert not calculate(network)["plans"]["centralized"]["feasible"]


def test_seasonal_rates_and_dt(network):
    site_water = network["sites"]["中心"]["water"]
    del site_water["wue_l_per_kwh_it"]
    site_water.update(wue_summer_l_per_kwh_it=2, wue_winter_l_per_kwh_it=1,
                      summer_hours=2, winter_hours=2)
    network.update(dt_hours=2, seasons=["summer", "winter"])
    central = calculate(network)["plans"]["centralized"]
    assert central["footprint"]["water_m3"] == (60 * 2 + 80) * 2
    assert central["footprint"]["carbon_t_co2"] == 168
    assert central["footprint"]["land_ha"] == 80


def test_zero_baseline_requires_reference_only_for_positive_weight(network):
    network["centralized"]["nodes"][0]["grid_co2_t_per_mwh"] = 0
    with pytest.raises(ValidationError, match="正基准"):
        calculate(network)
    network["reference_footprint"] = {"carbon_t_co2": 100, "water_m3": 210, "land_ha": 80}
    assert calculate(network)["plans"]["centralized"]["F"] == pytest.approx(math.log(0.6))
