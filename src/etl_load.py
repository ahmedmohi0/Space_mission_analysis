# =============================================================================
# SPACE MISSIONS — ETL PIPELINE
# =============================================================================
# Reads the raw CSV, cleans and transforms every column, builds dimension
# tables, and loads the full star schema into PostgreSQL.
#
# Pipeline order:
#   1. Load raw CSV
#   2. Clean & standardise columns
#   3. Parse special fields (Duration, Crew_Members, Partner_Agencies)
#   4. Build dimension tables  (dim_date, dim_agency, dim_launch)
#   5. Build fact table        (fact_missions)
#   6. Build bridge tables     (bridge_crew, bridge_partners)
#   7. Build mission meta      (dim_mission_meta)
#   8. Load all tables to PostgreSQL

import os
import re
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.config import RAW_DATA_DIR
from src.db import get_engine, query

from src.logger import setup_logging, get_logger


_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))




load_dotenv()

setup_logging()
log = get_logger(__name__)

CSV_PATH = RAW_DATA_DIR / "space_missions.csv"


# =============================================================================
#  LOAD RAW CSV
# =============================================================================

def load_raw(path: str) -> pd.DataFrame:
    log.debug(f"Reading CSV from: {path}")
    if not Path(path).exists():
        log.critical(f"CSV file not found at: {Path(path).resolve()}")
        raise FileNotFoundError(f"CSV not found: {path}")

    df = pd.read_csv(path, low_memory=False)
    log.info(f"Loaded raw CSV: {len(df):,} rows x {len(df.columns)} columns")
    return df


# =============================================================================
#  CLEAN & STANDARDISE
# =============================================================================
agency_founding_year = {
    "NASA": 1958,
    "CNES": 1961,
    "ISRO": 1969,
    "ESA": 1975,
    "ASI": 1988,
    "CSA": 1989,
    "Roscosmos": 1992,
    "CNSA": 1993,
    "DLR": 1997,
    "Blue Origin": 2000,
    "SpaceX": 2002,
    "JAXA": 2003,
}

_NA_STRINGS = {"n/a", "na", "none", "unknown", "not applicable", "", "nan"}


def _to_null(val):
   
    if val is None:
        return None
    if str(val).strip().lower() in _NA_STRINGS:
        return None
    return str(val).strip()

# Convert human-readable duration strings to float days.
def _parse_duration(val: str | None) -> float | None:

    if val is None:
        return None

    val = val.lower().replace("~", "").replace(",", "").strip()
    total_days = 0.0
    matched    = False

    patterns = [
        (r"([\d.]+)\s*year",  365.25),
        (r"([\d.]+)\s*month", 30.44),
        (r"([\d.]+)\s*day",   1.0),
        (r"([\d.]+)\s*hour",  1 / 24),
    ]

    for pattern, factor in patterns:
        m = re.search(pattern, val)
        if m:
            total_days += float(m.group(1)) * factor
            matched = True

    # Bare number -> assume days
    if not matched:
        m = re.fullmatch(r"[\d.]+", val)
        if m:
            return float(val)
        return None

    return round(total_days, 2) if total_days > 0 else None

#Log a warning if unexpected values appear in a categorical column.
def _validate_allowed(df, col, allowed: set):
    found      = set(df[col].dropna().unique())
    unexpected = found - allowed
    if unexpected:
        log.warning(f"Unexpected values in '{col}': {unexpected}")
    else:
        log.debug(f"'{col}' — all values within allowed set")


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
   
    log.info("Starting dataframe cleaning...")
    df = df.copy()

    # Column names: normalise to snake_case
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    log.debug("Column names normalised to snake_case")

    # String columns: strip whitespace, replace sentinels with None
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].apply(_to_null)
    log.debug(f"Sentinel values replaced with None across {len(str_cols)} string columns")

    # Dates
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
    df["end_date"]    = pd.to_datetime(df["end_date"],    errors="coerce")

    before = len(df)

    df['agency_founding_year'] = pd.to_datetime(df['agency'].map(agency_founding_year), format='%Y')
    df = df[df['launch_date'] >= df['agency_founding_year']]
    after = len(df)
    log.info("Launch dates validated against agency founding years")
    log.info(f"{after:,} rows remain after validation")
    log.info(f"{before - after:,} rows were deleted during validation")

    df["duration_days"] = df["duration"].apply(_parse_duration)
    parsed_ok   = df["duration_days"].notna().sum()
    parsed_fail = df["duration_days"].isna().sum()
    log.info(f"Duration parsed: {parsed_ok:,} valid, {parsed_fail:,} could not be parsed (set NULL)")

   
    df["cost_usd_million"] = pd.to_numeric(df["cost_usd_million"], errors="coerce")
    null_cost = df["cost_usd_million"].isna().sum()
    if null_cost:
        log.warning(f"{null_cost:,} rows have no cost data — will be NULL in fact table")
    df["cost_usd_million"] = df["cost_usd_million"] / 1000
    df = df.rename(columns={"cost_usd_million": "cost_usd_billion"})
    log.info("Cost converted from million USD to billion USD")
  

    
    _validate_allowed(df, "status",
        {"Success", "Failed", "Partial Success", "Ongoing", "Upcoming"})
    _validate_allowed(df, "mission_phase", {"Past", "Ongoing", "Future"})
    _validate_allowed(df, "crew_type",     {"Crewed", "Uncrewed"})
    _validate_allowed(df, "data_returned", {"Yes", "No", "Partial", None})

    log.info("Cleaning complete.")
    return df



# =============================================================================
#  BUILD DIMENSION TABLES
# =============================================================================

#Generate one row per calendar date covering the full range of launch_date and end_date in the dataset.
def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    
    log.debug("Building dim_date...")
    all_dates = pd.concat([
        df["launch_date"].dropna(),
        df["end_date"].dropna(),
    ]).dt.normalize().drop_duplicates().sort_values()

    dim = pd.DataFrame({"full_date": all_dates})
    dim["year"]       = dim["full_date"].dt.year
    dim["quarter"]    = dim["full_date"].dt.quarter
    dim["month"]      = dim["full_date"].dt.month
    dim["month_name"] = dim["full_date"].dt.strftime("%B")
    dim["week"]       = dim["full_date"].dt.isocalendar().week.astype(int)
    dim["day"]        = dim["full_date"].dt.day
    dim["decade"]     = (dim["year"] // 10 * 10).astype(str) + "s"
    dim = dim.reset_index(drop=True)
    dim.index += 1
    dim.index.name = "date_id"
    dim = dim.reset_index()

    log.info(f"dim_date built: {len(dim):,} rows  "
             f"({dim['year'].min()} — {dim['year'].max()})")
    return dim


def build_dim_agency(df: pd.DataFrame) -> pd.DataFrame:
    log.debug("Building dim_agency...")
    dim = (
        df[["agency", "country_region", "agency_type"]]
        .drop_duplicates()
        .dropna(subset=["agency"])
        .reset_index(drop=True)
    )
    dim.index += 1
    dim.index.name = "agency_id"
    dim = dim.reset_index()
    dim = dim.rename(columns={"agency": "agency_name"})

    log.info(f"dim_agency built: {len(dim):,} unique agencies")
    return dim


def build_dim_launch(df: pd.DataFrame) -> pd.DataFrame:

    log.debug("Building dim_launch...")
    dim = (
        df[["launch_vehicle", "launch_site"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim.index += 1
    dim.index.name = "launch_id"
    dim = dim.reset_index()

    log.info(f"dim_launch built: {len(dim):,} unique vehicle/site combinations")
    return dim


# =============================================================================
#  BUILD FACT TABLE
# =============================================================================

def build_fact_missions(
    df:         pd.DataFrame,
    dim_agency: pd.DataFrame,
    dim_launch: pd.DataFrame,
    dim_date:   pd.DataFrame,
) -> pd.DataFrame:

    log.debug("Building fact_missions...")
    fact = df.copy()

    # Resolve agency_id
    agency_map    = dim_agency.set_index("agency_name")["agency_id"]
    fact["agency_id"] = fact["agency"].map(agency_map)

    # Resolve launch_id
    launch_key    = dim_launch.set_index(["launch_vehicle", "launch_site"])["launch_id"]
    fact["launch_id"] = fact.apply(
        lambda r: launch_key.get((r["launch_vehicle"], r["launch_site"])),
        axis=1,
    )

    # Resolve date IDs
    date_map = dim_date.set_index("full_date")["date_id"]

    def _get_date_id(dt):
        if pd.isna(dt):
            return None
        return date_map.get(dt.normalize())

    fact["launch_date_id"] = fact["launch_date"].apply(_get_date_id)
    fact["end_date_id"]    = fact["end_date"].apply(_get_date_id)

    # Select columns
    fact = fact[[
        "mission_id", "agency_id", "launch_id", "launch_date_id", "end_date_id",
        "program_type", "mission_category", "sub_category", "destination",
        "status", "mission_phase", "crew_type", "data_returned",
        "failure_reason", "cost_usd_billion", "duration_days",
    ]]

    unresolved_agency = fact["agency_id"].isna().sum()
    unresolved_launch = fact["launch_id"].isna().sum()
    unresolved_date   = fact["launch_date_id"].isna().sum()

    if unresolved_agency:
        log.warning(f"{unresolved_agency} rows could not resolve agency_id")
    if unresolved_launch:
        log.warning(f"{unresolved_launch} rows could not resolve launch_id")
    if unresolved_date:
        log.warning(f"{unresolved_date} rows could not resolve launch_date_id")

    log.info(f"fact_missions built: {len(fact):,} rows")
    return fact


# =============================================================================
#  BUILD BRIDGE TABLES
# =============================================================================

def _explode_column(df: pd.DataFrame, src_col: str, out_col: str) -> pd.DataFrame:
    """
    Generic helper: split a comma-separated column into one row per value.
    Rows where the source column is None are dropped (no NULLs in bridge tables).
    """
    rows = []
    for _, row in df[["mission_id", src_col]].iterrows():
        if row[src_col] is None:
            continue
        for item in re.split(r",\s*", row[src_col]):
            item = item.strip()
            if item:
                rows.append({"mission_id": row["mission_id"], out_col: item})
    return pd.DataFrame(rows)


def build_bridge_crew(df: pd.DataFrame) -> pd.DataFrame:
    log.debug("Building bridge_crew...")
    bridge = _explode_column(df, "crew_members", "crew_member")
    crewed_missions = df[df["crew_type"] == "Crewed"]["mission_id"].nunique()
    log.info(f"bridge_crew built: {len(bridge):,} rows across {crewed_missions:,} crewed missions")
    return bridge


def build_bridge_partners(df: pd.DataFrame) -> pd.DataFrame:
    log.debug("Building bridge_partners...")
    bridge = _explode_column(df, "partner_agencies", "partner_agency")
    collab_missions = df[df["partner_agencies"].notna()]["mission_id"].nunique()
    log.info(f"bridge_partners built: {len(bridge):,} rows across {collab_missions:,} collaborative missions")
    return bridge


# =============================================================================
#  BUILD MISSION META
# =============================================================================

def build_dim_mission_meta(df: pd.DataFrame) -> pd.DataFrame:
    log.debug("Building dim_mission_meta...")
    meta = df[[
        "mission_id", "mission_name", "objective",
        "key_achievement", "mission_outcome_detail", "reference_url",
    ]].copy()
    log.info(f"dim_mission_meta built: {len(meta):,} rows")
    return meta


# =============================================================================
#  LOAD TO POSTGRESQL
# =============================================================================

def _truncate_all_tables(engine) -> None:
    """
    Empty all tables in one statement — TRUNCATE CASCADE handles
    FK order automatically.
    """
    with engine.connect() as conn:
        conn.execute(text("""
            TRUNCATE TABLE
                bridge_crew,
                bridge_partners,
                fact_missions,
                dim_mission_meta,
                dim_launch,
                dim_agency,
                dim_date
            RESTART IDENTITY CASCADE
        """))
        conn.commit()
    log.info("All tables truncated.")
    
_LOAD_ORDER = [
    ("dim_date",          "append"),
    ("dim_agency",        "append"),
    ("dim_launch",        "append"),
    ("dim_mission_meta",  "append"),
    ("fact_missions",     "append"),
    ("bridge_crew",       "append"),
    ("bridge_partners",   "append"),
]


def load_to_postgres(tables: dict, engine) -> None:
    """
    Load all tables in FK-safe order.
    tables: dict of {table_name: DataFrame}
    """
    log.info("Starting database load...")
    _truncate_all_tables(engine)
    for table_name, if_exists in _LOAD_ORDER:
        df = tables[table_name]
        log.info(f"Loading {table_name} ({len(df):,} rows)...")
        try:
            df.to_sql(
                name      = table_name,
                con       = engine,
                if_exists = if_exists,
                index     = False,
                method    = "multi",
                chunksize = 1000,
            )
            log.info(f"  {table_name} loaded successfully")
        except Exception as e:
            log.error(f"  Failed to load {table_name}: {e}")
            raise

    _apply_indexes(engine)


def _apply_indexes(engine) -> None:
    """Re-create indexes after table replace."""
    log.debug("Applying indexes...")
    statements = [
        "CREATE INDEX IF NOT EXISTS idx_fact_agency      ON fact_missions(agency_id)",
        "CREATE INDEX IF NOT EXISTS idx_fact_launch      ON fact_missions(launch_id)",
        "CREATE INDEX IF NOT EXISTS idx_fact_launch_date ON fact_missions(launch_date_id)",
        "CREATE INDEX IF NOT EXISTS idx_fact_end_date    ON fact_missions(end_date_id)",
        "CREATE INDEX IF NOT EXISTS idx_fact_status      ON fact_missions(status)",
        "CREATE INDEX IF NOT EXISTS idx_fact_phase       ON fact_missions(mission_phase)",
        "CREATE INDEX IF NOT EXISTS idx_fact_category    ON fact_missions(mission_category)",
        "CREATE INDEX IF NOT EXISTS idx_fact_crew_type   ON fact_missions(crew_type)",
        "CREATE INDEX IF NOT EXISTS idx_bridge_crew_mid  ON bridge_crew(mission_id)",
        "CREATE INDEX IF NOT EXISTS idx_bridge_part_mid  ON bridge_partners(mission_id)",
    ]
    with engine.connect() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
        conn.commit()
    log.info("Indexes applied.")


# =============================================================================
# MAIN
# =============================================================================

def run():
    log.info("=" * 60)
    log.info("SPACE MISSIONS ETL — START")
    log.info("=" * 60)

    engine = get_engine()

    raw     = load_raw(CSV_PATH)
    cleaned = clean_dataframe(raw)

    dim_date   = build_dim_date(cleaned)
    dim_agency = build_dim_agency(cleaned)
    dim_launch = build_dim_launch(cleaned)

    fact            = build_fact_missions(cleaned, dim_agency, dim_launch, dim_date)
    bridge_crew     = build_bridge_crew(cleaned)
    bridge_partners = build_bridge_partners(cleaned)
    dim_meta        = build_dim_mission_meta(cleaned)

    tables = {
        "dim_date":         dim_date,
        "dim_agency":       dim_agency,
        "dim_launch":       dim_launch,
        "dim_mission_meta": dim_meta,
        "fact_missions":    fact,
        "bridge_crew":      bridge_crew,
        "bridge_partners":  bridge_partners,
    }
    load_to_postgres(tables, engine)

    log.info("=" * 60)
    log.info("ETL COMPLETE — row counts:")
    for name, tbl in tables.items():
        log.info(f"  {name:<22} {len(tbl):>7,} rows")
    log.info("=" * 60)


if __name__ == "__main__":
    run()