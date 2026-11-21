# Evidence notes

Retrieved 2026-11-21. These are extraction notes, not translations or substitutes for the original sources.

## Oracle Stargate fact sheet

Source: `oracle_stargate_fact_sheet_2025-09-23.pdf`

- Abilene has eight buildings on 1,100 acres with up to about 4 million square feet.
- Abilene connects directly to ERCOT.
- The GE Vernova natural-gas plant is described as backup power.
- Closed-loop, non-evaporative liquid cooling is expected to use about 12,625 gallons per building per year for cooling-system maintenance and quality.
- The 360.5 MW generator site rating is therefore not included in the normal-operation Q1 base case.

## MISO project update

Source: `miso_hyperion_update_2025-07-10.pdf`

- Project: Cargas 500 kV and Smalling 500-230 kV stations.
- Entergy identifies a new load at Holly Ridge, Louisiana.
- `Spot Load Value (MW)`: 1,800.
- Expected in-service date: 2026-12-01.
- Project coordinates in the filing: approximately 32.479722 N, 91.636944 W.

This is a grid-load request and transmission project, not an IT-capacity measurement.

## MLGW xAI update

Source: `mlgw_xai_update_2025-05-05.pdf`

- About 150 MW was approved, connected through two substations, and energized.
- Another 150 MW remained contingent on approvals and construction.
- The update describes a curtailment commitment during high-demand periods.

The document is a dated utility snapshot. It does not establish the full Colossus site capacity.

## Meta Richland Parish

Source: <https://datacenters.atmeta.com/richland-parish-data-center/>

- Meta describes the Richland Parish data center as part of delivering 5 GW of compute capacity and calls Hyperion its largest multi-gigawatt AI cluster.
- The same operator page also describes the data center as delivering over 2 GW of compute capacity.
- The site uses closed-loop glycol cooling and dry cooling for most of the year.
- The page does not define whether "compute capacity" means IT power, facility power, or another compute metric.

This internal scope difference is why the data table retains multiple capacity fields.

## Fairwater Wisconsin water

Source: <https://www.wpr.org/news/microsoft-data-centers-8-million-gallons-water-each-year>

- City of Racine records show a peak of 0.702 MGD and 8.4 million gallons per year for subsequent phases.
- Phase 1 is 0.234 MGD and 2.8 million gallons per year.
- Microsoft purchased about 1,900 acres.
- The campus uses closed-loop cooling and is projected to consume zero water for cooling on most days, with an evaporative peak on the hottest days.

The MGD values are peaks, while the annual gallons are totals. They are not interchangeable.

## Compute Atlas records

The following records were accessed 2026-11-21 and are licensed CC BY 4.0:

- <https://www.compute-atlas.com/facilities/microsoft-mount-pleasant-wi>
- <https://www.compute-atlas.com/facilities/microsoft-fairwater-fayetteville-ga>
- <https://www.compute-atlas.com/facilities/amazon-project-rainier-new-carlisle-in>
- <https://www.compute-atlas.com/facilities/meta-hyperion-richland-parish-la>
- <https://www.compute-atlas.com/facilities/stargate-abilene-tx>
- <https://www.compute-atlas.com/facilities/xai-colossus-memphis-tn>
- <https://www.compute-atlas.com/facilities/xai-colossus-2-memphis-tn>

Each record links to its underlying operator, utility, permit, municipal, or news sources. Site-level acreage and Aqueduct water-stress labels in `curated/sites_master.csv` come from these records unless another source is explicitly named.
