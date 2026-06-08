# 🚀 Space Missions Analytics Pipeline (1957–2035)

A complete end-to-end data analytics project covering 65 years of space exploration — from data ingestion and cleaning through PostgreSQL warehousing, statistical analysis, and machine learning, to a Power BI report.

---


## 📌 Project Status

**Phase 1 — Infrastructure:** ✅ Complete  
**Phase 2 — Python Notebooks:** 🔄 In Progress (Notebook 01 complete)  
**Phase 3 — Power BI Report:**   
**Phase 4 — Portfolio Publish:**   

---

## 📂 Dataset

| Property | Detail |
|---|---|
| Source | [Kaggle](https://www.kaggle.com/datasets/maulikgajera/global-space-missions-dataset-19502025) |
| Coverage | 1957–2035 (78 years of space history) |
| Rows | ~10,500 missions |
| Columns | 26 |


### Dataset Columns

| Column | Type | Description |
|----------|----------|----------|
| `mission_id` | String | Unique mission identifier |
| `mission_name` | String | Official mission name |
| `program_type` | String | Mission program type (e.g. Robotic, Human Spaceflight, Satellite) |
| `mission_category` | String | High-level mission category (e.g. Moon, Mars, Earth Orbit) |
| `sub_category` | String | Specific mission type (e.g. Orbiter, Lander, Rover, CubeSat) |
| `destination` | String | Target destination or operational region |
| `status` | String | Mission status (Success, Failed, Partial Success, Ongoing, Upcoming) |
| `mission_phase` | String | Temporal classification (Past, Ongoing, Future) |
| `crew_type` | String | Crewed or Uncrewed mission |
| `data_returned` | String | Indicates whether scientific or operational data was returned |
| `failure_reason` | String | Failure description for unsuccessful missions |
| `cost_usd_billion` | Float | Mission cost in billions of USD |
| `duration_days` | Float | Mission duration in days |
| `agency_name` | String | Responsible space agency or organization |
| `country_region` | String | Country or region associated with the mission |
| `agency_type` | String | Agency classification (Government or Private) |
| `launch_vehicle` | String | Launch vehicle used for the mission |
| `launch_site` | String | Launch facility or spaceport |
| `launch_date` | Date | Mission launch date |
| `launch_year` | Integer | Launch year extracted from launch date |
| `launch_decade` | String | Launch decade (e.g. 1960s, 2000s, 2020s) |
| `end_date` | Date | Mission end date (NULL for ongoing or future missions) |
| `end_year` | Integer | End year extracted from end date |
| `end_decade` | String | End decade (e.g. 1970s, 2010s) |
| `objective` | String | Primary mission objective |
| `key_achievement` | String | Major accomplishment or milestone achieved |
| `mission_outcome_detail` | String | Detailed description of mission outcome |
| `reference_url` | String | Source url|

---


## Project Architecture

This project was designed as a complete analytical pipeline rather than a standalone notebook workflow.

The dataset is first cleaned and validated in Python, transformed into an analytical star-schema structure, and then loaded into PostgreSQL using a custom ETL pipeline.

The project separates:

* Raw data ingestion
* Data cleaning and validation
* Schema transformation
* Database loading
* Analytical querying

This modular structure improves maintainability, scalability, and reproducibility.

space_mission_analysis/
│
├── data/
│   └── raw/
│       └── space_missions.csv
│
├── notebooks/
│   ├── 01_data_cleaning.ipynb       
│   ├── 02_eda.ipynb                 
│   ├── 03_historical_analysis.ipynb 
│   ├── 04_failure_analysis.ipynb    
│   ├── 05_clustering.ipynb          
│   ├── 06_classification.ipynb      
│   ├── 07_time_series.ipynb         
│   └── 08_anomaly_detection.ipynb   
│
├── src/
│   ├── config.py
│   ├── db.py
│   └── logger.py
│
├── etl_load.py
├── schema.sql
├── requirements.txt
├── .env                             (not committed)
└── README.md
```

---

## 🗄️ Database Design

The raw CSV was transformed into a **star schema** PostgreSQL warehouse to support efficient analytical querying and Power BI integration.

### Schema Diagram

```
                    ┌─────────────────┐
                    │   dim_date      │
                    │─────────────────│
                    │ date_id (PK)    │
                    │ full_date       │
                    │ year / quarter  │
                    │ month / week    │
                    │ decade          │
                    └────────┬────────┘
                             │
┌────────────────┐   ┌───────┴──────────┐   ┌─────────────────┐
│  dim_agency    │   │  fact_missions   │   │  dim_launch     │
│────────────────│   │──────────────────│   │─────────────────│
│ agency_id (PK) ├───┤ mission_id (PK)  ├───┤ launch_id (PK)  │
│ agency_name    │   │ agency_id (FK)   │   │ launch_vehicle  │
│ country_region │   │ launch_id (FK)   │   │ launch_site     │
│ agency_type    │   │ launch_date_id   │   └─────────────────┘
└────────────────┘   │ end_date_id      │
                     │ program_type     │   ┌──────────────────────┐
                     │ mission_category │   │  dim_mission_meta    │
                     │ sub_category     │   │──────────────────────│
                     │ destination      ├───┤ mission_id (PK)      │
                     │ status           │   │ mission_name         │
                     │ mission_phase    │   │ objective            │
                     │ crew_type        │   │ key_achievement      │
                     │ data_returned    │   │ mission_outcome_detail│
                     │ failure_reason   │   │ reference_url        │
                     │ cost_usd_billion │   └──────────────────────┘
                     │ duration_days    │
                     └───────┬──────────┘
                             │
              ┌──────────────┴───────────────┐
              │                              │
   ┌──────────┴──────────┐      ┌────────────┴────────────┐
   │    bridge_crew      │      │   bridge_partners       │
   │─────────────────────│      │─────────────────────────│
   │ id (PK)             │      │ id (PK)                 │
   │ mission_id (FK)     │      │ mission_id (FK)         │
   │ crew_member         │      │ partner_agency          │
   └─────────────────────┘      └─────────────────────────┘
```

### Tables

| Table | Rows (approx.) | Purpose |
|---|---|---|
| `fact_missions` | ~4,630 | Core mission facts and measures |
| `dim_date` | ~7,648 | Calendar dimension for launch and end dates |
| `dim_agency` | ~11 | Agency descriptors |
| `dim_launch` | ~121 | Launch vehicle and site combinations |
| `dim_mission_meta` | ~4,630 | Mission objectives and outcomes |
| `bridge_crew` | variable | Many-to-many: missions ↔ crew members |
| `bridge_partners` | variable | Many-to-many: missions ↔ partner agencies |

### Analytical Views

| View | Purpose |
|---|---|
| `vw_agency_summary` | Mission counts, success rates, and costs per agency |
| `vw_yearly_trend` | Annual launch volumes and outcomes by decade |
| `vw_destination_summary` | Mission counts and success rates by destination |

---

## ⚙️ ETL Pipeline (`etl_load.py`)

The ETL pipeline reads the raw CSV, applies all cleaning and transformation logic, builds the star schema in memory, and loads it into PostgreSQL.

### Pipeline Steps

1. **Load raw CSV** — reads `space_missions.csv`
2. **Clean & standardise** — strips whitespace, converts sentinel strings (`n/a`, `none`, `unknown`) to `NULL`, normalises column names to `snake_case`
3. **Parse special fields** — converts human-readable duration strings (e.g. `"2 years 3 months"`) to `duration_days` (float); converts `cost_usd_million` → `cost_usd_billion`
4. **Validate** — allowed-value checks on `status`, `mission_phase`, `crew_type`, `data_returned`; date validation against agency founding years; removal of records where `end_date < launch_date`
5. **Build dimensions** — `dim_date`, `dim_agency`, `dim_launch`
6. **Build fact table** — resolves foreign keys from dimension lookups
7. **Build bridge tables** — explodes comma-separated crew and partner columns into normalised rows
8. **Build mission meta** — `dim_mission_meta` for objective and outcome text
9. **Load to PostgreSQL** — truncates all tables, loads in FK-safe order, re-creates indexes

### Key Cleaning Decisions

| Issue | Action |
|---|---|
| Sentinel strings (`n/a`, `none`, etc.) | Replaced with `NULL` |
| Duration as free text | Parsed with regex into `duration_days` (float) |
| Cost in millions | Converted to billions (`/ 1000`) |
| `end_date < launch_date` (164 records) | Removed as temporally invalid |
| Structural nulls (`failure_reason` for successes, `end_date` for ongoing missions) | Preserved — these are intentionally null |
| Converting the flat file to a star schema stored in postgres eliminated all structural nulls and ensures data get stored in a clean and normalized way |
| Duplicate mission names across agencies | Retained — confirmed as separate missions |
| Agencies with missions before the agency got created |

---


## 🛠️ Requirements

```
pandas
numpy
sqlalchemy
psycopg2-binary
python-dotenv
matplotlib
seaborn
scikit-learn
xgboost
shap
prophet
jupyter
```

Install with:

```bash
pip install -r requirements.txt
```

---

## 🚀 Quickstart

### 1. Clone and set up the environment

```bash
git clone https://github.com/your-username/space-mission-analysis.git
cd space-mission-analysis
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure credentials

Create a `.env` file in the project root:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=space_missions
DB_USER=your_user
DB_PASSWORD=your_password
```

### 3. Create the database schema

Connect to PostgreSQL and run:

```bash
psql -U your_user -d space_missions -f schema.sql
```

### 4. Run the ETL pipeline

```bash
python etl_load.py
```

### 5. Verify the load

The ETL will call `health_check()` automatically. You should see all 7 tables populated in the log output.

### 6. Open the notebooks

```bash
jupyter notebook notebooks/
```

---

## 📊 Tech Stack

| Layer | Technology |
|---|---|
| Data Storage | PostgreSQL 15 |
| ETL & Analysis | Python 3.11, pandas, SQLAlchemy |
| Machine Learning | scikit-learn, XGBoost, SHAP, Prophet |
| Visualisation | matplotlib, seaborn |
| BI Dashboard | Power BI Desktop |
| Version Control | Git / GitHub |

---

## 📁 Key Files

| File | Purpose |
|---|---|
| `schema.sql` | Creates all tables, indexes, and analytical views |
| `etl_load.py` | Full ETL pipeline — CSV to PostgreSQL |
| `src/db.py` | Database connection helpers and query utilities |
| `src/logger.py` | Centralised logging setup |
| `src/config.py` | Path configuration for data directories |
| `notebooks/01_data_cleaning.ipynb` | Data validation and cleaning documentation |
| `.env` | Database credentials (not committed) |

---

*Project by [Ahmed Mohi]  built as a full-stack data analytics portfolio project.*