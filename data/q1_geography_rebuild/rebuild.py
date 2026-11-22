"""Rebuild Q1 screens from geometry, weather and explicit network design scenarios."""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "q1_five_sites"))
from reproduce import calculate, config, load_weather, profile

# site, gross area (ha), roof catchment proxy (m²), white space proxy (m²),
# voltage (kV), facility multiplier, water use (L/kWh IT)
# Where only a parcel is known, assume 50% roof coverage and half of one
# floor for IT. SG and AU have reported floor areas; see README.
SITES = [
    ("us_golden", 0.186, 930, 930, 13.2, 1.06, 0.7),
    ("is_keflavik", 16, 80000, 40000, 33, 1.20, 0.02),
    ("sg_tanjongkling", 12*0.40468564224, 170000/11, 85000, 66, 1.19, 2.4),
    ("cl_quilicura", 15.9, 13600, 6800, 110, 1.08, 0.5),
    ("au_huntingwood", 8.3, 41500, 35000, 132, 1.15, 1.2),
    ("is_keflavik", 2.4, 12000, 6000, 132, 1.20, 0.02),
]


def rain_yield(rain, roof):
    # 80% captured, 50 L storage per square metre. At cyclic steady state,
    # every cumulative drawdown must fit the tank, including across year end.
    inflow = rain * roof * 0.0008
    tank = roof * 0.05
    low, high = 0.0, inflow.mean()
    for _ in range(40):
        rate = (low + high) / 2
        balance = np.r_[0., np.cumsum(np.tile(inflow - rate, 2))]
        if np.max(np.maximum.accumulate(balance) - balance) <= tank:
            low = rate
        else:
            high = rate
    return low


def run():
    rows = []
    for key, area, roof, white_space, voltage, k, wue in SITES:
        folder = HERE.parent / ("q1_" + key)
        metadata = json.loads((folder / "parameters.json").read_text())
        time, weather = load_weather(folder)
        hours = time.astype("datetime64[Y]") == np.datetime64("2025")
        rain = rain_yield(weather["precipitation_mm"], roof)
        land = math.floor(white_space / 6) * 0.1
        site = key if area != 2.4 else "is_keflavik_extension"
        # Solve the original hourly cyclic battery dispatch once. Roof PV has
        # zero additional land and water in this design and scales additively
        # with firm grid delivery under the original behind-the-meter model.
        v = dict(grid=0, k=k, Q=rain, wue=wue, A=area, A0=0, a=area/land,
                 roof_m2=roof*0.2)
        cfg = config(site, v, profile(weather)[hours], "2025 solar, 2016–25 water")
        result = calculate(cfg)
        pv = result["scenarios"][1]["breakdown"]["self_generation_mw"]
        for occupancy in (0., 0.5, 0.8, 1.):
            # One surviving path after loss of its twin. Occupancy includes
            # existing and committed non-study loads. Upstream must support it.
            grid = math.sqrt(3)*voltage*0.6*0.95*(1-occupancy)
            power = (grid+pv)/k
            if occupancy == 0.5:
                cfg["P_grid_mw"] = grid
                check = calculate(cfg)["P_max_mw_it"]
                assert np.isclose(check, min(power, rain/wue, land))
            rows.append(dict(site=site, lat=metadata["weather_source"]["requested_lat"],
                lon=metadata["weather_source"]["requested_lon"], area_ha=area,
                catchment_m2=roof, white_space_m2=white_space, voltage_kV=voltage,
                occupied_fraction=occupancy, scenario_grid_MW=grid, k=k, wue=wue,
                roof_PV_peak_MW=roof*.2*.00018, roof_PV_firm_MW=pv,
                assured_rain_m3_h=rain, power_limit_IT=power, land_limit_IT=land,
                rain_limit_IT=rain/wue, rain_only_IT=min(power, land, rain/wue),
                sufficient_external_water_IT=min(power, land),
                extra_water_needed_m3_h=max(0,min(power,land)*wue-rain)))
    with (HERE/'results.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    run()
