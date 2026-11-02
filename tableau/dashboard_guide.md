# Tableau implementation guide

Connect to `tableau/data/census_2011_commute_modes.csv`. Label every dashboard as **Census 2011 work commute data**. Filter `mode_of_travel = All Modes` out of mode composition and distance charts, while retaining it as a denominator/total where appropriate. Start with `residence_area = Urban` if focusing on the named urban districts; expose Total/Rural/Urban as a filter.

## Four supported dashboards

1. **Executive Commute Overview** — Urban All Modes worker-count KPI by geography, mode share bars, and gender counts. State the 2011 reference year.
2. **Geographic Comparison** — Mode composition by district/UT with residence filter. The Punjab geography is district aggregate; Mohali uses Sahibzada Ajit Singh Nagar district.
3. **Distance to Work** — Distance band counts by commute mode and residence class.
4. **Gender & Mode** — Census male/female/person count comparisons by mode and geography.

## Calculated fields

**Commute Mode (exclude total row)**
```text
[mode_of_travel] <> "All Modes"
```

**Female share of persons**
```text
SUM([total_female]) / SUM([total_persons])
```

**Distance band label** can be derived by pivoting source distance columns in Tableau Prep or by using the already named `*_persons` columns as measures. Do not treat distance buckets as trip-level records.

## Parameters, sets, filters and actions

- Add a Residence Area parameter or quick filter for Total/Urban/Rural.
- Create a Top N geography set by `SUM(total_persons)` for the selected mode. Make clear it ranks census aggregates.
- Group source modes only for a documented presentation purpose; preserve the original mode field for auditability.
- Add filters for geography, residence area, mode and year.
- Add a dashboard filter action from geography comparison to distance/gender views, with a reset option.
- KPI cards may show worker counts, mode share, and reference year. Do not create revenue, cancellation, booking, or hour-of-day KPIs from this source.
- Assign a geographic role to `area_name` only after Tableau resolves the Indian district/UT correctly; validate against a Punjab/Chandigarh map before using a filled map. If district geocoding is ambiguous, retain the bar chart. The source has no pickup coordinates or neighborhood geometry.
- A dual-axis chart is not needed for the available counts; avoid one unless a clearly compatible secondary measure is added and both axes remain readable.

Tableau Desktop/Public authoring and publishing are manual. No workbook or public dashboard link is included yet.
