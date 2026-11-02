# Supported Census metrics

| Metric | Definition | Fields | Interpretation |
|---|---|---|---|
| Worker commute count | Census person count for selected mode/geography/residence | total_persons | Workers in the B-28 “other workers” universe, Census 2011 |
| Mode share | Mode count ÷ same area/residence All Modes count | total_persons, mode_of_travel, mode_share_pct | Share of this worker commute aggregate, not share of ride bookings |
| Commute distance count | Workers by reported one-way distance band | distance bucket `*_persons` | Distance from residence to workplace per source definition |
| Gender counts | Census male/female/person counts | `*_male`, `*_female`, `*_persons` | Aggregate source counts; not user-level data |

The extract cannot support ride bookings, booking trends, peak hours, fare/revenue, cancellation rate, or ride-hailing vehicle performance. Keep the All Modes row out of mode-composition charts because it is the denominator total, not an additional mode.
