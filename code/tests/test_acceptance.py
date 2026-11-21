import json
import sys
from pathlib import Path

import pytest
import yaml
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from immc_power_capacity.app import main, run
from immc_power_capacity.core import (
    ValidationError,
    combined_battery,
    grid_only,
    hydro,
    solar,
    solve_storage_capacity,
    thermal,
    total_capacity,
    wind,
)


def test_grid_only():
    result = grid_only(120, 1.20)
    assert result["breakdown"]["facility_mw"] == 120
    assert result["breakdown"]["it_mw"] == 100


def test_solar_without_battery_is_zero_when_night_zero():
    result = solar("PV", 120, 1.20, 1, 100, [0.2, 0], 1)
    assert result["breakdown"]["self_generation_mw"] == pytest.approx(0)
    assert result["method"]["L_mw"] == pytest.approx(0)
    assert result["method"]["curtailment_mw"] == pytest.approx([20, 0])


def test_solar_battery_manual_case():
    result = solar(
        "PV+Battery", 120, 1.20, 1, 100, [0.2, 0], 1,
        {"C_max_mw": 10, "D_max_mw": 10, "E_usable_mwh": 10,
         "charge_efficiency": 1, "discharge_efficiency": 1},
    )
    assert result["breakdown"]["self_generation_mw"] == pytest.approx(10)
    assert result["method"]["charge_mw"] == pytest.approx([10, 0], abs=1e-8)
    assert result["method"]["discharge_mw"] == pytest.approx([0, 10], abs=1e-8)
    assert result["method"]["energy_start_mwh"] == pytest.approx([0, 10], abs=1e-8)


def test_solar_battery_accepts_raw_mw_series():
    result = solar(
        "PV+Battery", 120, 1.20, 1, 100, dt_hours=1, net_output_mw=[20, 0],
        battery={"C_max_mw": 10, "D_max_mw": 10, "E_usable_mwh": 10},
    )
    assert result["breakdown"]["self_generation_mw"] == pytest.approx(10)
    assert result["method"]["input_series"] == "net_output_mw"


def test_storage_energy_dynamics_and_no_simultaneous_charge_discharge():
    load, schedule = solve_storage_capacity([20, 0], 1, 10, 10, 10, 1, 1)
    assert load == pytest.approx(10)
    charge = schedule["charge_mw"]
    discharge = schedule["discharge_mw"]
    energy = schedule["energy_start_mwh"]
    for index, (c_value, d_value) in enumerate(zip(charge, discharge)):
        assert min(c_value, d_value) == pytest.approx(0, abs=1e-8)
        next_energy = energy[index] + c_value - d_value
        expected = energy[(index + 1) % len(energy)]
        assert next_energy == pytest.approx(expected, abs=1e-8)


def test_storage_with_non_unit_dt():
    load, schedule = solve_storage_capacity([20, 0], 2, 10, 10, 10, 1, 1)
    assert load == pytest.approx(5)
    assert max(schedule["charge_mw"]) == pytest.approx(5)
    assert max(schedule["discharge_mw"]) == pytest.approx(5)


@pytest.mark.parametrize(
    "supply,dt,c_max,d_max,energy,eta_c,eta_d",
    [
        ([20, 0], 1, 10, 10, 10, 1, 1),
        ([5, 0, 3], 1, 2, 2, 4, 0.9, 0.9),
        ([8, 1, 0, 4], 2, 3, 3, 6, 0.95, 0.9),
    ],
)
def test_dispatch_attains_independent_lp_bound(supply, dt, c_max, d_max, energy, eta_c, eta_d):
    load, dispatch = solve_storage_capacity(supply, dt, c_max, d_max, energy, eta_c, eta_d)
    periods = len(supply)
    objective = [0.0] * (1 + 3 * periods)
    objective[0] = -1
    power = []
    for index in range(periods):
        row = [0.0] * (1 + 3 * periods)
        row[0] = 1
        row[1 + index] = 1
        row[1 + periods + index] = -1
        power.append(row)
    energy_rows = []
    for index in range(periods):
        row = [0.0] * (1 + 3 * periods)
        row[1 + index] = -eta_c * dt
        row[1 + periods + index] = dt / eta_d
        row[1 + 2 * periods + index] -= 1
        row[1 + 2 * periods + (index + 1) % periods] += 1
        energy_rows.append(row)
    result = linprog(
        objective,
        A_ub=power,
        b_ub=supply,
        A_eq=energy_rows,
        b_eq=[0] * periods,
        bounds=[(0, None)] + [(0, c_max)] * periods + [(0, d_max)] * periods
        + [(0, energy)] * periods,
        method="highs",
    )
    assert result.success
    assert load == pytest.approx(result.x[0], abs=1e-6)
    for index, available in enumerate(supply):
        charge = dispatch["charge_mw"][index]
        discharge = dispatch["discharge_mw"][index]
        stored = dispatch["energy_start_mwh"][index]
        assert 0 <= charge <= c_max + 1e-8 and 0 <= discharge <= d_max + 1e-8
        assert 0 <= stored <= energy + 1e-8
        assert min(charge, discharge) == 0
        assert available + discharge == pytest.approx(load + charge + dispatch["curtailment_mw"][index])
        assert dispatch["energy_start_mwh"][(index + 1) % periods] == pytest.approx(
            stored + dt * (eta_c * charge - discharge / eta_d), abs=1e-8)


def test_combined_wind_solar_battery():
    result = combined_battery(
        "风光共用电池", 120, 1.2, [20, 0], 110, 1,
        {"C_max_mw": 10, "D_max_mw": 10, "E_usable_mwh": 10},
    )
    assert result["breakdown"]["self_generation_mw"] == pytest.approx(10)
    assert "equation" in result["method"]
    assert "energy_start_mwh" in result["method"]


def test_wind_hydro_and_fuel_heat():
    wind_result = wind(
        "wind", 120, 1.2, area_km2=10, density_mw_per_km2=8,
        net_output_mw=[8, 20, 16],
    )
    assert wind_result["breakdown"]["self_generation_mw"] == pytest.approx(8)
    assert wind_result["method"]["alpha"] == pytest.approx(0.1)

    hydro_result = hydro("hydro", 120, 1.2, 100, 100, 80, 0.9)
    assert hydro_result["breakdown"]["self_generation_mw"] == pytest.approx(70.632)

    gas_result = thermal("gas", 120, 1.2, 2, 50, 0.4, True)
    assert gas_result["method"]["fuel_heat_needed_mw"] == pytest.approx(250)


def test_invalid_inputs():
    with pytest.raises(ValidationError):
        total_capacity(120, 0, 0.99)
    with pytest.raises(ValidationError):
        wind("wind", 120, 1.2, area_km2=-1, density_mw_per_km2=6, alpha=0.2)
    with pytest.raises(ValidationError):
        wind("wind", 120, 1.2, area_km2=1, density_mw_per_km2=6, alpha=1.2)
    with pytest.raises(ValidationError):
        wind("wind", 120, 1.2, installed_mw=10, net_output_mw=[15, 12])
    with pytest.raises(ValidationError):
        solar("PV", 120, 1.2, 1, 100, [0.2, None], 1)
    with pytest.raises(ValidationError):
        solar("PV", 120, 1.2, 1, 100, [0.2], 1, {"E_usable_mwh": 10})
    with pytest.raises(ValidationError):
        thermal("gas", 120, 1.2, 1, 50, 0.4, False)
    with pytest.raises(ValidationError):
        thermal("coal", 120, 1.2, 1.5, 50)
    with pytest.raises(ValidationError):
        solar("PV", 120, 1.2, 1, 100, [0.2], 1,
              {"C_max_mw": 10, "D_max_mw": 10, "E_usable_mwh": 10,
               "charge_efficiency": 0})


def test_cli_example_names_and_outputs(tmp_path):
    json_path = tmp_path / "result.json"
    report = run(ROOT / "examples" / "example_supply.yaml", json_path)
    names = [item["name"] for item in report["scenarios"]]
    assert "纯电网" in names
    assert "光伏+电池" in names
    assert report["optimum"]["name"] == "煤电"
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    solar_storage = next(item for item in saved["scenarios"] if item["name"] == "光伏+电池")
    for field in ("charge_mw", "discharge_mw", "energy_start_mwh", "curtailment_mw"):
        assert field in solar_storage["method"]
    overlap = max(
        min(c_value, d_value)
        for c_value, d_value in zip(
            solar_storage["method"]["charge_mw"],
            solar_storage["method"]["discharge_mw"],
        )
    )
    assert overlap == pytest.approx(0, abs=1e-8)


def test_cli_manual_acceptance_config():
    report = run(ROOT / "examples" / "acceptance_manual.yaml")
    rows = {item["name"]: item for item in report["scenarios"]}
    assert rows["纯电网"]["breakdown"]["it_mw"] == pytest.approx(100)
    assert rows["光伏无电池"]["breakdown"]["self_generation_mw"] == pytest.approx(0)
    storage = rows["光伏+电池"]
    assert storage["breakdown"]["self_generation_mw"] == pytest.approx(10)
    assert storage["breakdown"]["facility_mw"] == pytest.approx(130)
    assert storage["breakdown"]["it_mw"] == pytest.approx(108.33333333333334)


def test_cli_rejects_mwh_as_mw(tmp_path, capsys):
    config = {
        "P_grid_mw": 120,
        "k_factor": 1.2,
        "scenarios": [{
            "type": "solar",
            "name": "错误单位",
            "area_km2": 1,
            "density_mw_per_km2": 100,
            "dt_hours": 1,
            "net_output_mw": [20, 0],
            "battery": {
                "C_max_mw": 10,
                "D_max_mw": 10,
                "E_usable_mw": 10,
            },
        }],
    }
    path = tmp_path / "bad_unit.yaml"
    path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    code = main([str(path)])
    captured = capsys.readouterr()
    assert code == 2
    assert "E_usable_mw" in captured.err
    assert "MWh" in captured.err


def test_cli_rejects_missing_series(tmp_path, capsys):
    config = {
        "P_grid_mw": 120,
        "k_factor": 1.2,
        "scenarios": [{
            "type": "solar",
            "name": "缺序列",
            "area_km2": 1,
            "density_mw_per_km2": 100,
            "dt_hours": 1,
        }],
    }
    path = tmp_path / "missing.yaml"
    path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    code = main([str(path)])
    captured = capsys.readouterr()
    assert code == 2
    assert "supply_ratios" in captured.err


def test_cli_rejects_mva_as_mw(tmp_path, capsys):
    config = {
        "P_grid_mva": 150,
        "k_factor": 1.2,
        "scenarios": [{"type": "grid", "name": "纯电网"}],
    }
    path = tmp_path / "mva.yaml"
    path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    code = main([str(path)])
    captured = capsys.readouterr()
    assert code == 2
    assert "P_grid_mva" in captured.err
    assert "P_grid_mw" in captured.err
