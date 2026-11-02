"""RidePulse ingestion, validation, cleaning, and Tableau export pipeline."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
TABLEAU_DIR = ROOT / "tableau" / "data"
PUNJAB_CITIES = {"chandigarh", "mohali", "ludhiana", "amritsar", "jalandhar", "patiala"}
TARGET_DISTRICTS = {"jalandhar": "Jalandhar", "ludhiana": "Ludhiana", "patiala": "Patiala", "amritsar": "Amritsar", "sahibzada ajit singh nagar": "Mohali"}
DISTRICT_CODES = {"037", "041", "048", "049", "052"}
DISTANCE_BINS = ["no_travel", "0_1_km", "2_5_km", "6_10_km", "11_20_km", "21_30_km", "31_50_km", "51_plus_km", "distance_not_stated"]
GENDERS = ["persons", "male", "female"]
CITY_ALIASES = {"s.a.s. nagar": "Mohali", "s.a.s nagar": "Mohali", "sas nagar": "Mohali", "mohali": "Mohali"}
REQUIRED = {"city"}
ALIASES = {
    "bookingid": "booking_id", "ride_id": "booking_id", "trip_id": "booking_id",
    "date": "booking_datetime", "datetime": "booking_datetime", "booking_time": "booking_datetime",
    "pickup_city": "city", "service_city": "city", "vehicle_category": "vehicle_type",
    "distance_km": "distance_km", "trip_distance_km": "distance_km", "fare_amount": "fare",
    "duration_minutes": "duration_min", "trip_duration_min": "duration_min",
    "status": "booking_status", "pickup_area": "pickup_location", "dropoff_area": "dropoff_location",
}

def normalize_columns(columns: Any) -> dict[str, str]:
    result = {}
    for col in columns:
        key = re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower()).strip("_")
        result[col] = ALIASES.get(key, key)
    return result

def _read(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)

def inspect_sources(paths: list[Path] | None = None) -> dict[str, Any]:
    """Inventory supplied source files without modifying them."""
    sources = paths if paths is not None else sorted([*RAW_DIR.glob("*.csv"), *RAW_DIR.glob("*.xlsx"), *RAW_DIR.glob("*.xls")])
    report: dict[str, Any] = {"status": "no_source_files", "source_count": 0, "sources": [],
        "coverage_rule": sorted(PUNJAB_CITIES), "kpi_support": {},
        "note": "No source dataset supplied. No observed booking statistics can be calculated."}
    for path in sources:
        try:
            df = _read(path)
            if "B-28" in path.name.upper() or "B28" in path.name.upper():
                report["sources"].append({"file": path.name, "records": int(max(len(df)-6, 0)), "columns": ["state_code", "district_code", "residence_area", "area_name", "mode_of_travel", "total persons by distance and gender"],
                    "geographic_coverage": "2011 Census Punjab or Chandigarh; targeted district/UT aggregates", "missing_values": "multi-row Census header; normalized by process_census_b28",
                    "kpi_support": {"commute mode counts": True, "commute distance distribution": True, "gender counts": True,
                        "ride bookings": False, "fare": False, "cancellation": False, "booking time": False}})
                continue
            columns = list(normalize_columns(df.columns).values())
            report["sources"].append({"file": path.name, "records": int(len(df)), "columns": columns,
                "geographic_coverage": "unverified until city validation", "missing_values": {str(k): int(v) for k,v in df.isna().sum().items()},
                "kpi_support": {"bookings": "city + booking rows" if "city" in columns else "unsupported: city missing",
                    "time trends": "booking_datetime" in columns, "cancellations": "booking_status" in columns,
                    "fare": "fare" in columns, "distance": "distance_km" in columns,
                    "vehicle": "vehicle_type" in columns, "locations": "pickup_location" in columns or "dropoff_location" in columns}})
        except Exception as exc:
            report["sources"].append({"file": path.name, "error": str(exc)})
    report["source_count"] = len(report["sources"])
    report["status"] = "inspected" if sources else "no_source_files"
    return report

def process_census_b28(path: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Normalize the official Census 2011 B-28 workbook to tidy commute-mode rows.

    The official workbooks have six metadata/header rows. The universe is "other
    workers" and the geography is district/UT aggregates, not ride transactions.
    """
    path = Path(path)
    raw = pd.read_excel(path, sheet_name=0, header=None)
    if raw.shape[1] < 36 or "B0128" not in raw.iloc[:, 0].astype(str).values:
        raise ValueError(f"{path.name} does not match the official Census B-28 layout (36 columns and B0128 rows expected).")
    rows = raw.iloc[6:].copy()
    rows = rows[rows.iloc[:, 0].astype(str).str.strip().eq("B0128")].copy()
    source_records = len(rows)
    rows.columns = range(raw.shape[1])
    rows[1] = rows[1].astype(str).str.zfill(2)
    rows[2] = rows[2].astype(str).str.zfill(3)
    rows[3] = rows[3].astype(str).str.strip()
    rows[4] = rows[4].astype(str).str.strip()
    rows[5] = rows[5].astype(str).str.strip()
    is_punjab = path.name.upper().startswith("DDW-0300")
    if is_punjab:
        rows = rows[rows[2].isin(DISTRICT_CODES)]
        rows = rows[rows[3].isin(["Total", "Urban", "Rural"])]
    else:
        rows = rows[rows[1].eq("04") & rows[2].eq("055") & rows[3].isin(["Total", "Urban", "Rural"])]
    frame = pd.DataFrame({
        "area_name": rows[4].str.lower().map(TARGET_DISTRICTS).fillna(rows[4].str.title()),
        "source_area_name": rows[4],
        "district_code": rows[2],
        "residence_area": rows[3],
        "mode_of_travel": rows[5],
        "year": 2011,
        "source_file": path.name,
    }, index=rows.index)
    frame["geography_level"] = "District/UT aggregate"
    frame["state_or_ut"] = "Punjab" if is_punjab else "Chandigarh"
    frame["source_universe"] = "Other workers (Census 2011)"
    measures = ["total"]
    measures.extend(DISTANCE_BINS)
    col = 6
    for measure in measures:
        for gender in GENDERS:
            name = f"{measure}_{gender}"
            frame[name] = pd.to_numeric(rows.iloc[:, col], errors="coerce").to_numpy()
            col += 1
    total_col = "total_persons"
    denominator = frame[frame.mode_of_travel.eq("All Modes")].set_index(["area_name", "residence_area"])[total_col]
    frame["mode_share_pct"] = [round(100 * value / denominator.get((area, res), np.nan), 2) if pd.notna(value) and denominator.get((area, res), 0) else np.nan
        for area, res, value in zip(frame.area_name, frame.residence_area, frame[total_col])]
    # Total rows repeat the state/UT-level aggregate; the retained geography is district/UT-level only.
    frame = frame.reset_index(drop=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True); TABLEAU_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "punjab" if is_punjab else "chandigarh"
    cleaned = OUT_DIR / f"census_2011_commute_modes_{suffix}.csv"
    tableau = TABLEAU_DIR / f"census_2011_commute_modes_{suffix}.csv"
    frame.to_csv(cleaned, index=False); frame.to_csv(tableau, index=False)
    report = {"source_file": path.name, "records_read": int(source_records), "records_output": int(len(frame)),
        "coverage": sorted(frame.area_name.unique().tolist()), "year": 2011,
        "universe": "Other workers", "grain": "one row per geography, residence area (Total/Urban/Rural), and travel mode",
        "columns": list(frame.columns), "missing_values": {str(k): int(v) for k,v in frame.isna().sum().items()},
        "kpi_support": {"commute mode counts": True, "distance to work distribution": True, "gender counts": True,
            "bookings": False, "fare/revenue": False, "cancellations": False, "hourly/monthly trends": False},
        "cleaned_file": str(cleaned.relative_to(ROOT)), "tableau_file": str(tableau.relative_to(ROOT)),
        "source_url": "https://censusindia.gov.in/nada/index.php/catalog/13957" if is_punjab else "https://censusindia.mha.gov.in/nada/index.php/catalog/13958"}
    (OUT_DIR / f"census_2011_commute_modes_{suffix}_quality.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return frame, report

def process_file(path: str | Path, output_dir: str | Path = OUT_DIR) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Clean one source, retaining questionable rows and flagging them explicitly."""
    path = Path(path)
    raw = _read(path)
    original_rows = len(raw)
    raw = raw.rename(columns=normalize_columns(raw.columns))
    raw.columns = [str(c).strip().lower() for c in raw.columns]
    missing_required = REQUIRED - set(raw.columns)
    if missing_required:
        raise ValueError(f"Missing required column(s): {', '.join(sorted(missing_required))}. Required: city.")
    df = raw.copy()
    for col in ("city", "vehicle_type", "booking_status", "pickup_location", "dropoff_location"):
        if col in df:
            df[col] = df[col].astype("string").str.strip()
    df["city"] = df["city"].str.lower().map(lambda x: CITY_ALIASES.get(x, x.title()) if pd.notna(x) else x)
    df["city"] = df["city"].replace({"Chandigarh": "Chandigarh", "Ludhiana": "Ludhiana", "Amritsar": "Amritsar", "Jalandhar": "Jalandhar", "Patiala": "Patiala"})
    df["quality_flag"] = ""
    invalid_city = ~df.city.fillna("").str.lower().isin(PUNJAB_CITIES)
    df.loc[invalid_city, "quality_flag"] = "city_missing_or_out_of_scope"
    if "booking_datetime" in df:
        df["booking_datetime"] = pd.to_datetime(df.booking_datetime, errors="coerce")
        bad = df.booking_datetime.isna()
        df.loc[bad & df.quality_flag.eq(""), "quality_flag"] = "invalid_booking_datetime"
        df["booking_hour"] = df.booking_datetime.dt.hour.astype("Int64")
        df["day_of_week"] = df.booking_datetime.dt.day_name()
        df["month"] = df.booking_datetime.dt.to_period("M").astype("string")
        df["is_weekend"] = df.booking_datetime.dt.dayofweek.ge(5).where(df.booking_datetime.notna(), pd.NA).astype("boolean")
    for col in ("fare", "distance_km", "duration_min"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            bad = df[col].notna() & (df[col] < 0)
            df.loc[bad & df.quality_flag.eq(""), "quality_flag"] = f"negative_{col}"
    if "fare" in df:
        df["revenue"] = df.fare.where(df.fare.ge(0))
    duplicate_mask = df.duplicated(keep="first")
    if "booking_id" in df:
        duplicate_mask |= df.booking_id.notna() & df.booking_id.duplicated(keep="first")
    df["is_duplicate"] = duplicate_mask
    df.loc[duplicate_mask & df.quality_flag.eq(""), "quality_flag"] = "duplicate_record"
    df["source_file"] = path.name
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    cleaned_path = out / f"{path.stem}_cleaned.csv"
    df.to_csv(cleaned_path, index=False)
    TABLEAU_DIR.mkdir(parents=True, exist_ok=True)
    tableau_path = TABLEAU_DIR / f"{path.stem}_tableau.csv"
    df.to_csv(tableau_path, index=False)
    report = {"source_file": path.name, "records_read": int(original_rows), "records_output": int(len(df)),
        "columns": list(df.columns), "missing_values": {str(k): int(v) for k,v in df.isna().sum().items()},
        "out_of_scope_or_missing_city": int(invalid_city.sum()), "duplicates_flagged": int(duplicate_mask.sum()),
        "quality_flags": {str(k): int(v) for k,v in df.loc[df.quality_flag.ne(""), "quality_flag"].value_counts().items()},
        "cleaned_file": str(cleaned_path.relative_to(ROOT)), "tableau_file": str(tableau_path.relative_to(ROOT)),
        "cleaning_policy": "Rows retained; questionable rows flagged. Negative measures retained and flagged."}
    (out / f"{path.stem}_quality.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return df, report

def run_pipeline() -> list[dict[str, Any]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted([*RAW_DIR.glob("*.csv"), *RAW_DIR.glob("*.xlsx"), *RAW_DIR.glob("*.xls")])
    if not files:
        raise FileNotFoundError(f"No CSV or Excel source files found in {RAW_DIR}. Add a Punjab-focused dataset and rerun.")
    reports = []
    census_files = []
    for path in files:
        if "B-28" in path.name.upper() or "B28" in path.name.upper():
            frame, report = process_census_b28(path)
            census_files.append(frame)
            reports.append(report)
        else: reports.append(process_file(path)[1])
    if census_files:
        combined = pd.concat(census_files, ignore_index=True)
        OUT_DIR.mkdir(parents=True, exist_ok=True); TABLEAU_DIR.mkdir(parents=True, exist_ok=True)
        combined.to_csv(OUT_DIR / "census_2011_commute_modes.csv", index=False)
        combined.to_csv(TABLEAU_DIR / "census_2011_commute_modes.csv", index=False)
        summary = {"source_files": [report["source_file"] for report in reports if "B-28" in report["source_file"].upper()],
            "records_output": int(len(combined)), "coverage": sorted(combined.area_name.unique().tolist()), "year": 2011,
            "quality_flags": "No row-level values imputed; Census structural Total/Urban/Rural aggregates retained.",
            "kpi_support": {"commute mode counts": True, "distance distribution": True, "gender counts": True,
                "ride bookings": False, "fare": False, "cancellations": False, "booking time": False}}
        (OUT_DIR / "census_2011_commute_modes_quality.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return reports

if __name__ == "__main__":
    try:
        print(json.dumps(run_pipeline(), indent=2))
    except Exception as exc:
        raise SystemExit(f"Pipeline stopped: {exc}")
