USE ridepulse;

-- Urban worker counts by travel mode; the Census total row is intentionally excluded.
SELECT area_name, mode_of_travel, total_persons, mode_share_pct
FROM commute_modes
WHERE residence_area = 'Urban' AND census_year = 2011 AND mode_of_travel <> 'All Modes'
ORDER BY area_name, total_persons DESC;

-- Mode share comparison by geography, using persons in matching urban aggregates.
SELECT area_name, mode_of_travel, mode_share_pct
FROM commute_modes
WHERE residence_area = 'Urban' AND census_year = 2011 AND mode_of_travel <> 'All Modes'
ORDER BY mode_of_travel, mode_share_pct DESC;

-- Gender counts by mode and residence class.
SELECT area_name, residence_area, mode_of_travel,
       SUM(total_male) AS male_workers, SUM(total_female) AS female_workers,
       SUM(total_persons) AS workers
FROM commute_modes
WHERE census_year = 2011 AND mode_of_travel <> 'All Modes'
GROUP BY area_name, residence_area, mode_of_travel
ORDER BY area_name, residence_area, workers DESC;

-- Distance-band commute counts for urban aggregates.
SELECT area_name, mode_of_travel,
       SUM(no_travel_persons) AS no_travel,
       SUM(distance_0_1_km_persons) AS km_0_1,
       SUM(distance_2_5_km_persons) AS km_2_5,
       SUM(distance_6_10_km_persons) AS km_6_10,
       SUM(distance_11_20_km_persons) AS km_11_20,
       SUM(distance_21_30_km_persons) AS km_21_30,
       SUM(distance_31_50_km_persons) AS km_31_50,
       SUM(distance_51_plus_km_persons) AS km_51_plus,
       SUM(distance_not_stated_persons) AS distance_not_stated
FROM commute_modes
WHERE residence_area = 'Urban' AND census_year = 2011 AND mode_of_travel <> 'All Modes'
GROUP BY area_name, mode_of_travel;

-- Rank modes within geography/residence using a CTE and window function.
WITH mode_counts AS (
  SELECT area_name, residence_area, mode_of_travel, total_persons
  FROM commute_modes
  WHERE census_year = 2011 AND mode_of_travel <> 'All Modes'
)
SELECT area_name, residence_area, mode_of_travel, total_persons,
       DENSE_RANK() OVER (PARTITION BY area_name, residence_area ORDER BY total_persons DESC) AS mode_rank
FROM mode_counts;
