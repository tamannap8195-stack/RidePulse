# RidePulse — Punjab & Chandigarh Mobility Intelligence

RidePulse currently uses **real, attributable public data only**: Office of the Registrar General & Census Commissioner, India, Population Census 2011, Table B-28. The downloaded Punjab and Chandigarh Excel workbooks are stored under `data/raw/`. They describe workers’ commute mode and one-way distance to work. They are not ride-hailing bookings.

## Integrated sources and scope

| Workbook | Source | Raw worksheet rows | Extracted analysis rows | Geography in this project |
|---|---|---:|---:|---|
| `DDW-0300B-28.xlsx` | [Punjab Census B-28 (2011)](https://censusindia.gov.in/nada/index.php/catalog/13957) | 693 B0128 data rows, plus six headers | 165 | Amritsar, Jalandhar, Ludhiana, Patiala, Sahibzada Ajit Singh Nagar district (labelled Mohali district) |
| `DDW-0400B-28.xlsx` | [Chandigarh Census B-28 (2011)](https://censusindia.mha.gov.in/nada/index.php/catalog/13958) | 66 B0128 data rows, plus six headers | 33 | Chandigarh district/UT |

The source table describes “other workers” by travel mode, residence class (Total/Urban/Rural), gender counts, and commute distance buckets. The cleaned data has one row per area, residence class, and travel mode. The six Punjab district/UT aggregates are not all equivalent to city proper; Mohali is represented by Sahibzada Ajit Singh Nagar district. Chandigarh is sourced separately because it is a Union Territory.

**Ride-hailing limitations:** this source has no booking IDs, pickups/drop-offs, booking timestamps, fare, cancellation status, or app vehicle booking categories. RidePulse therefore does not calculate ride demand, revenue, cancellation rates, peak booking hours, or operational KPIs from this data. Auto/Taxi commute counts are not ride-hailing bookings. The 2011 figures are historical and should not be presented as current mobility levels.

## Features

- Reusable ingestion for CSV/Excel and a Census B-28 normalizer for the included multi-row-header workbooks.
- Tableau-ready Census extract, data dictionary, KPI definitions, and four supported dashboard plans.
- Streamlit portal for geography/residence filters, commute-mode and distance charts, table exploration, and CSV export.
- Optional MySQL tables and SQL queries for the actual normalized commute metrics.

## Install and run (PowerShell)

```powershell
.\setup.ps1
.\run.ps1
```

Open the URL printed by Streamlit, usually `http://localhost:8501`.

Rebuild the normalized extract after changing/replacing source workbooks:

```powershell
.\.venv\Scripts\python.exe pipeline.py
```

Outputs:

- `data/processed/census_2011_commute_modes.csv` — combined analysis file.
- `data/processed/census_2011_commute_modes_quality.json` — quality and support report.
- `tableau/data/census_2011_commute_modes.csv` — Tableau source.

The raw `.xlsx` workbooks are checked in with the project and separately attributed in [`data/source_notes.md`](data/source_notes.md). Do not put unrelated or synthetic files in `data/raw`.

## Tableau

Tableau is the primary interactive BI tool; Streamlit is the supporting data portal. Connect Tableau to `tableau/data/census_2011_commute_modes.csv`. See [data dictionary](tableau/data_dictionary.md), [KPI definitions](tableau/kpi_definitions.md), and [dashboard guide](tableau/dashboard_guide.md). The four dashboards focus on commute overview, geography, distance and gender/mode. Tableau workbook creation and publishing still require Tableau Desktop/Public.

## MySQL (optional)

Copy `.env.example` to `.env` and set local credentials. Then initialize and load the normalized real dataset with `python database.py --init --load`; query examples are in `sql/analytics.sql`. Credentials are not stored in the repository. Database tables represent Census commute aggregates, not bookings.

## Method and quality

The B-28 workbooks contain six metadata/header rows followed by Census rows. The pipeline checks the expected B0128 layout, retains target district/UT aggregates across Total/Urban/Rural, assigns clearly named distance/gender columns, adds mode share using each geography/residence All Modes total, and keeps source filenames. There are no missing values in the 198-row normalized extract. The field-level missingness and KPI-support audit is in `data/processed/census_2011_commute_modes_quality.json`. It does not infer bookings or create records.

## Screenshots and findings

No Tableau workbook or screenshots are claimed. The app calculates views from the official extracts when the pipeline is run. Findings should be described as 2011 worker commute patterns only. Do not generalize them to all residents, all trips, current demand, or app-based taxi activity.
