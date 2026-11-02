# Tableau data dictionary — Census 2011 B-28 commute extract

Connect to `tableau/data/census_2011_commute_modes.csv`. This is an official aggregate table of “other workers” by work commute mode and one-way distance. One row is a geography × residence class × travel mode.

| Field | Meaning |
|---|---|
| area_name | Display geography; Mohali is the Sahibzada Ajit Singh Nagar district aggregate |
| source_area_name | Original Census area label |
| district_code | Census district code; Chandigarh uses district code 055 |
| residence_area | Census aggregate: Total, Urban, or Rural |
| mode_of_travel | Census mode label, including All Modes and No travel |
| year | Census reference year (2011) |
| state_or_ut | Punjab or Chandigarh |
| geography_level | District/UT aggregate; not neighborhood-level |
| source_universe | Census population universe: Other workers |
| total_persons / total_male / total_female | Count for the mode and geography |
| no_travel_*, 0_1_km_*, 2_5_km_* … distance_not_stated_* | Counts by source one-way distance interval and gender |
| mode_share_pct | Mode count divided by same area/residence All Modes count |
| source_file | Downloaded source workbook name |

No booking, pickup, drop-off, fare, cancellation, vehicle booking type or time-of-day fields exist in this source.
