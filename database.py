"""Optional MySQL setup helpers. Credentials are read from environment variables."""
import os
from pathlib import Path
import argparse
import pandas as pd
from dotenv import load_dotenv

SCHEMA_PATH = Path(__file__).parent / "sql" / "schema.sql"
load_dotenv(Path(__file__).parent / ".env")

def get_connection(include_database=True):
    try:
        import mysql.connector
    except ImportError as exc:
        raise RuntimeError("Install mysql-connector-python to use the optional MySQL integration.") from exc
    args = {"host": os.getenv("MYSQL_HOST", "localhost"), "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"), "password": os.getenv("MYSQL_PASSWORD", "")}
    if include_database: args["database"] = os.getenv("MYSQL_DATABASE", "ridepulse")
    return mysql.connector.connect(**args)

def initialize_schema():
    connection = get_connection(include_database=False)
    try:
        cursor = connection.cursor()
        for statement in SCHEMA_PATH.read_text(encoding="utf-8").split(";"):
            if statement.strip(): cursor.execute(statement)
        connection.commit()
    finally:
        connection.close()

def load_commute_data(csv_path=None):
    """Load the normalized official Census extract into MySQL, idempotently."""
    path = Path(csv_path) if csv_path else Path(__file__).parent / "data" / "processed" / "census_2011_commute_modes.csv"
    if not path.exists(): raise FileNotFoundError(f"Normalized dataset not found: {path}. Run python pipeline.py first.")
    frame = pd.read_csv(path)
    columns = ["area_name", "source_area_name", "district_code", "state_or_ut", "residence_area", "mode_of_travel", "census_year",
        "total_persons", "total_male", "total_female", "no_travel_persons", "distance_0_1_km_persons", "distance_2_5_km_persons",
        "distance_6_10_km_persons", "distance_11_20_km_persons", "distance_21_30_km_persons", "distance_31_50_km_persons",
        "distance_51_plus_km_persons", "distance_not_stated_persons", "mode_share_pct", "source_file"]
    mapping = {"census_year": "year"}
    values = []
    for row in frame.to_dict("records"):
        values.append(tuple(None if pd.isna(row.get(mapping.get(col, col))) else row.get(mapping.get(col, col)) for col in columns))
    updates = ", ".join(f"{col}=VALUES({col})" for col in columns if col not in {"area_name", "residence_area", "mode_of_travel", "census_year"})
    placeholders = ", ".join(["%s"] * len(columns))
    query = f"INSERT INTO commute_modes ({', '.join(columns)}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.executemany(query, values)
        connection.commit()
        return len(values)
    finally:
        connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare/load the real Census commute dataset in MySQL.")
    parser.add_argument("--init", action="store_true", help="Create the database and commute table")
    parser.add_argument("--load", action="store_true", help="Load the normalized Census CSV (run pipeline.py first)")
    args = parser.parse_args()
    if args.init: initialize_schema()
    if args.load:
        count = load_commute_data()
        print(f"Loaded {count} Census commute aggregate rows into MySQL.")
    if not args.init and not args.load: parser.print_help()
