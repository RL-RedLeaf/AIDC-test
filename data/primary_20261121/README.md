# Abilene case study: validity correction

**The Abilene capacity results in outputs 02-05 and 10-11, 14, plus `visualize/fig06_*`, are withdrawn. Do not cite 769 MW IT, 3,062 MW IT, their sensitivity values, or comparisons based on them as model findings.** The script used Mortenson's 1 GW station engineering capacity as if it were firm, continuously deliverable site import, then divided by assumed `k=1.30`. It also calculated land capacity using self-selected rack/layout factors rather than a documented physical land-use intensity. Those calculations were arithmetically consistent with the entered assumptions but did not follow the required evidence standard.

The publicly documented geometry still supports these conversions: 1,100 acres = 445.15 ha gross campus; 12.5 acres = 5.06 ha substation; approximately 4 million sqft = 371,612 m2 total building floor area. These are not enough to derive `P_E` or `P_L`. See [output 15 validity audit](outputs/15_validity_audit.csv) for every numbered result's status and missing primary evidence. Earlier outputs are retained as a historical record; they are not a valid Abilene calculation.

**Current defensible conclusion:** the three-resource maximum `P_max` is not identified from the public primary inputs collected so far. No replacement MW estimate is asserted. The old build script is intentionally disabled so it cannot silently recreate the withdrawn result.

## Required inputs to resume

- Electricity: transformer nameplate ratings and bank connections, bus/feeder limits, utility system-impact or interconnection study, and existing/committed simultaneous load. These establish sustainable net MW at the campus boundary. Then obtain a matched facility-versus-IT design power budget for `k`. A 345 kV voltage and a station project capacity alone do not determine continuous MW.
- Land: parcel polygons and constraints to determine effective area, plus actual hall/building allocation and a documented marginal site-area-per-IT-MW relationship. The published gross area and total floor area are evidence, but rack cell, hall fraction and floor/site assumptions in the former script were not project facts.
- Water: site allocation and design-hour delivery, together with same-boundary design WUE. The planning table's annual municipal numbers and the operator's annual maintenance estimates do not establish these quantities.

No reverse calibration is permitted: Epoch's IT estimate, delivered project MW, or another reported target capacity cannot be used to infer `k`, WUE, `a_site` or grid delivery and then validate that same target.

The original 2026-11-21 outputs and source downloads remain below for audit history. Their source-claim tables may still be useful as leads, subject to the status in output 15.

---

# Historical analysis (withdrawn)

The material below describes the former screening, not a valid Abilene result. Do not use its capacity values or regenerate its figures.

This is a new static case study. It does not import any model parameter from the deleted `data/` results. The only cross-site estimate, Epoch's current IT MW, is read **after** Q1 calculations for comparison. All published outputs are in `outputs/`; `00_output_index.csv` records each numbered file's inputs, meaning, conditions and use.

The Q1 JSON's 769 MW result is an electricity-land screening ceiling under a zero variable-WUE assumption, not a validated three-resource `P_max`. Here `P_W=null` because no site-specific design WUE and matching project water delivery have been identified. Oracle's annual cooling-maintenance estimate is retained as a separate annual check, not inserted into a design-hour WUE. The comparison table names this result a screening ceiling. Do not cite it as the maximum sustainable scale until the water constraint is established.

Run from the repository root:

```powershell
python data/primary_20261121/scripts/build_abilene.py
```

## Interpretation

The 2030 Abilene case assumes an already completed eight-building campus under normal operation. It is a **conditional physical screening ceiling**, not an actual project rating, grid contract, permit or verified sustainable allowance. The 1 GW, 345 kV station figure comes from its construction contractor, who reports five main transformers, a spare, and energization by March 2026. Individual transformer MVA and simultaneous upstream/old-station usage are not disclosed. We therefore use only this station's 1 GW engineering rating, never sum it with the older 200 MW station, and explicitly assume the full rating can be delivered. Acquiring the utility's upstream margin is the most important remaining measurement.

The 2026 Region G water plan's 2030 column gives 45,587 acre-ft/year total Abilene supply and 34,116 acre-ft/year total demand. The difference assumes full access to the listed contracts and is annualized to m3/h solely to enter Q1. It is **not** a verified hourly rate or a project water right. The plan separately reports a smaller regulatory planning surplus under its database rules. The non-evaporative cooling scenario uses WUE=0 for *variable cooling water*, and checks Oracle's fixed eight-building maintenance refill separately; the current Q1 model has no fixed-water term. Domestic/process water and pumping limits are unmeasured.

For the single design-night configuration, the annualized municipal margin is **assumed** to be continuously deliverable in that same design condition. This is a matching-period scenario assumption, not a deduction from the water plan; hourly treatment capacity and dry-period availability still need primary evidence.

The raw input lists the five water-source components, municipal demand, 17 sales contracts and eight recommended additional demands separately. Their sums are checked against, but are not taken from, the plan's printed totals. The 2026 plan also reports a 4,496 acre-ft/year projected 2030 surplus under its DB27 water-availability rules, versus the 11,471 acre-ft/year potential contract-access difference used here. This discrepancy is a material uncertainty. The source-level planning yields themselves are not a reproduction of the underlying reservoir hydrology or full WAM/WRAP allocation model.

The effective land initially equals the gross 1,100 acres, so it is an optimistic site-area bound. Its marginal ha/MW is built from the published four million sqft *total floor area* plus declared rack rating, rack cell and IT-hall share. None uses project IT MW. A one-story assumption is used only to display the implied building footprint fraction; a different story count cannot change capacity when total floor area is held fixed. The contractor's 12.5-acre substation is deducted as a fixed area, assuming it lies within the site. GIS ecological, flood and ownership exclusions have not been validated. The output also reports sensitivity to effective land fraction and the full-load facility/IT multiplier, without tuning either to Epoch.

The Epoch snapshot's current Abilene IT estimate describes a different stage than the fully built 2030 screening case. A numerical difference is informative, but it is not a validation statistic. Other major centers appear in a comparison-only inventory; their primary electrical, water and parcel records are still needed before a defensible three-constraint run.

Outputs 12-13 reconcile newer operator water disclosures. Crusoe's 2026 impact report page says a generic 200 MW facility uses about 910,000 US gallons/year total, while its 2026 water-stewardship diagram gives about 2,000,000 gallons/year for a generic 200 MW facility and breaks the total into cooling maintenance, employee indoor use and custodial use. These are conflicting estimates until the operator clarifies scope/version. Separately, Crusoe's Abilene page estimates 50,000 gallons/building/year for cooling maintenance; Oracle's September 2025 fact sheet estimates 12,625 gallons/building/year. The difference may reflect scope or revision, but the public sources do not reconcile it. Preserve each as a source-specific claim; do not average them or treat them as design-hour values.

The equivalent-WUE sensitivity in output 13 divides each generic 200 MW annual-water claim by an assumed annual IT-energy denominator derived from the same report's PUE range (1.2-1.4) and explicit 75%-100% IT-load cases. The range is an illustrative archetype calculation, not measured Abilene WUE, not a cooling WUE, and not an input to Q1. It shows the denominator and scope sensitivity: total site water includes employee and custodial water, while WUE reporting boundaries may focus on facility water relative to IT energy.

The additional on-site PV option is a deliberately unbuilt design comparison. Its AC installation density comes from the declared 600 W module, 5 m2/module land cell and 0.8 AC/DC ratio. In the static night design hour without a battery it produces zero firm increment, while reserving 50 ha that cannot simultaneously hold IT infrastructure. No annual weather series or expansion trajectory is simulated.

## Abilene electricity-land findings

For this case, the two quantified scenario limits are

```text
P_E = P_grid / k = 1,000 / 1.30 = 769.2 MW IT
P_L = (445.15 - 5.06) / 0.143748 = 3,061.6 MW IT
P_E-L = min(P_E, P_L) = 769.2 MW IT
```

`P_E-L` is explicitly an electricity-land screening ceiling, not a three-resource sustainable maximum. The power side assumes the contractor's 1 GW 345 kV station rating is all firm deliverable project power; the land side assumes all 1,100 acres can be used and applies a declared rack/layout intensity. Under those base assumptions electricity is the active constraint and land has about four times as much calculated headroom. The result is therefore much more sensitive to actual grid delivery and the assumed facility/IT factor than to small land corrections.

Output 14 solves the threshold at which land would replace electricity as the E-L bottleneck. Under the same 1 GW delivery assumption, the crossover effective land shares are about 29.2% at k=1.15, 26.0% at k=1.30, and 24.2% at k=1.40. Below the relevant share land binds; above it electricity binds. These thresholds inherit the gross-site and layout assumptions and are not GIS-derived parcel availability.

At the base k=1.30, an effective land share of 25% gives a land ceiling of about 739 MW IT, slightly below the 769 MW electricity ceiling; at 50% land availability the electricity cap binds again. Thus the current screening result has a clear conditional reading: **if** about one quarter or less of the gross site survives planning, ecological, flood, access and other exclusions, land may cap this layout first; otherwise the assumed electrical delivery is the smaller of the two quantified limits.

Output 11 compares the conditional Abilene screening number with the problem's 950 MW, 2,263 MW and 5 GW figures as magnitudes only. Other sites and the ambiguous 5 GW compute-power boundary make these unsuitable as direct error statistics. The model's own 2030 fully built scenario versus Epoch's *current* Abilene estimate also has a stage mismatch, kept visible in output 05.

Output 09 includes a Malaysian operator case. DayOne combines Nusajaya and Kempas on its Johor page and gives inconsistent combined 390 MW and over 478 MW figures. Its Kempas announcement specifies a Phase 2 treatment-plant total of 20 million L/day expected in Q3 2027, but neither an individual-site firm electricity input nor the renewable river yield and site land budget. No Q1 maximum is asserted for this site.
