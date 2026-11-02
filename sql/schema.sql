CREATE DATABASE IF NOT EXISTS ridepulse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ridepulse;

CREATE TABLE IF NOT EXISTS commute_modes (
  record_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  area_name VARCHAR(120) NOT NULL,
  source_area_name VARCHAR(160) NOT NULL,
  district_code VARCHAR(8) NOT NULL,
  state_or_ut VARCHAR(30) NOT NULL,
  residence_area VARCHAR(20) NOT NULL,
  mode_of_travel VARCHAR(80) NOT NULL,
  census_year SMALLINT NOT NULL,
  total_persons BIGINT,
  total_male BIGINT,
  total_female BIGINT,
  no_travel_persons BIGINT,
  distance_0_1_km_persons BIGINT,
  distance_2_5_km_persons BIGINT,
  distance_6_10_km_persons BIGINT,
  distance_11_20_km_persons BIGINT,
  distance_21_30_km_persons BIGINT,
  distance_31_50_km_persons BIGINT,
  distance_51_plus_km_persons BIGINT,
  distance_not_stated_persons BIGINT,
  mode_share_pct DECIMAL(7,3),
  source_file VARCHAR(255),
  UNIQUE KEY uq_census_row (area_name, residence_area, mode_of_travel, census_year),
  INDEX idx_geography_mode (area_name, mode_of_travel),
  INDEX idx_year_residence (census_year, residence_area)
);
