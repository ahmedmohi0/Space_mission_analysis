
import os
from os import path
import pandas as pd
from sqlalchemy import URL, create_engine, text
from dotenv import load_dotenv
from src.logger import get_logger
from sqlalchemy.engine import url 
load_dotenv()
#module level logger
log = get_logger(__name__)



_engine = None
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_NAME")


#Creating engine and query functions

#returns a sql alchemy engine instance, creating it if it doesn't exist yet. Uses environment variables for connection details and logs the process.
def get_engine():
   
    global _engine
    if _engine is None:
        log.debug("No existing engine — creating a new one.")

        required = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
        missing  = [k for k in required if not os.getenv(k)]
        if missing:
            log.critical(f"Missing environment variables: {missing}")
            raise EnvironmentError(
                f"Missing environment variables: {missing}\n"
                f"Make sure your .env file exists and is filled in."
            )

        url = URL.create(
            drivername="postgresql+psycopg2",
            username=user,
            password=password,
            host=host,
            port=port,
            database=database)
        try:
            _engine = create_engine(url, echo=False)
            log.info(
                f"Database engine initialised — "
                f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/"
                f"{os.getenv('DB_NAME')}"
            )
        except Exception as e:
            log.critical(f"Failed to create database engine: {e}")
            raise
    else:
        log.debug("Reusing existing engine.")

    return _engine



#This function executes a SQL query against the database and returns the results as a pandas DataFrame. It logs the query execution and handles any exceptions that may occur, providing informative error messages.

def query(sql: str, params: dict = None) -> pd.DataFrame:
  
    log.debug(f"Executing query: {sql[:120].strip()}{'...' if len(sql) > 120 else ''}")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        if df.empty:
            log.warning(f"Query returned 0 rows — verify filters are correct.")
        else:
            log.debug(f"Query returned {len(df):,} rows.")
        return df
    except Exception as e:
        log.error(f"Query failed: {e}")
        raise

#This function simply reads an entire table into the dataframe using pandas read_sql the point of it is just to have a quick way to load a whole table without writing SQL, but it should be used sparingly for large tables to avoid memory issues.

def query_table(table_name: str) -> pd.DataFrame:
    
    return pd.read_sql_table(table_name, con=get_engine())




#fact_missions joined with dim_agency, dim_launch, and dim_date,Returns one wide DataFrame,No text/meta columns.
    
def load_missions_full() -> pd.DataFrame:

    sql = """
        SELECT
            f.mission_id,
            f.program_type,
            f.mission_category,
            f.sub_category,
            f.destination,
            f.status,
            f.mission_phase,
            f.crew_type,
            f.data_returned,
            f.failure_reason,
            f.cost_usd_million,
            f.duration_days,

            a.agency_name,
            a.country_region,
            a.agency_type,

            l.launch_vehicle,
            l.launch_site,

            d.full_date      AS launch_date,
            d.year           AS launch_year,
            d.quarter        AS launch_quarter,
            d.month          AS launch_month,
            d.decade         AS launch_decade

            d2.full_date      AS end_date,
            d2.year           AS end_year,
            d2.quarter        AS end_quarter,
            d2.month          AS end_month,
            d2.decade         AS end_decade
        FROM fact_missions  f
        LEFT JOIN dim_agency  a ON f.agency_id       = a.agency_id
        LEFT JOIN dim_launch  l ON f.launch_id        = l.launch_id
        LEFT JOIN dim_date    d ON f.launch_date_id   = d.date_id
        left join dim_date d2 on f.end_date_id = d2.date_id
        ORDER BY d.full_date
    """
    df = query(sql)
    log.info(f"load_missions_full → {len(df):,} rows")
    return df

#Same as load_missions_full() but also includes the narrative text columns
def load_missions_with_meta() -> pd.DataFrame:
    
    sql = """
        SELECT
            f.mission_id,
            m.mission_name,
            f.program_type,
            f.mission_category,
            f.sub_category,
            f.destination,
            f.status,
            f.mission_phase,
            f.crew_type,
            f.data_returned,
            f.failure_reason,
            f.cost_usd_million,
            f.duration_days,

            a.agency_name,
            a.country_region,
            a.agency_type,

            l.launch_vehicle,
            l.launch_site,

            d.full_date      AS launch_date,
            d.year           AS launch_year,
            d.decade         AS launch_decade,

            d2.full_date      AS end_date,
            d2.year           AS end_year,
            d2.decade         AS end_decade,

            m.objective,
            m.key_achievement,
            m.mission_outcome_detail,
            m.reference_url
        FROM fact_missions    f
        LEFT JOIN dim_agency       a ON f.agency_id       = a.agency_id
        LEFT JOIN dim_launch       l ON f.launch_id        = l.launch_id
        LEFT JOIN dim_date         d ON f.launch_date_id   = d.date_id
        LEFT JOIN dim_mission_meta m ON f.mission_id       = m.mission_id
        left join dim_date d2 on f.end_date_id = d2.date_id
        ORDER BY d.full_date
    """
    df = query(sql)
    log.info(f"load_missions_with_meta → {len(df):,} rows")
    return df



# Quick sanity check — logs row counts for all core tables.this will be run at the top of a new notebook to confirm everything is loaded correctly and the DB is reachable. 
def health_check() -> None:
   
    tables = [
        "dim_date", "dim_agency", "dim_launch",
        "dim_mission_meta", "fact_missions",
        "bridge_crew", "bridge_partners",
    ]
    log.info("── Database Health Check ─────────────────────")
    all_ok = True
    for t in tables:
        try:
            result = query(f"SELECT COUNT(*) AS n FROM {t}")
            n = result["n"].iloc[0]
            if n == 0:
                log.warning(f"  {t:<25} 0 rows — table is empty")
                all_ok = False
            else:
                log.info(f"  {t:<25} {n:>7,} rows")
        except Exception as e:
            log.error(f"  {t:<25} FAILED — {e}")
            all_ok = False

    if all_ok:
        log.info("Health check passed — all tables populated.")
    else:
        log.warning("Health check completed with warnings — review logs above.")
    log.info("──────────────────────────────────────────────")
