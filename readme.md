# 🚀 Space Missions Analytics Pipeline (1957–2022)

An end-to-end data analytics project covering 65 years of space exploration history — from raw data ingestion and cleaning, through a PostgreSQL star-schema warehouse, to statistical analysis and a Power BI report.

I built this to answer a real question, not just to showcase tools: **has spaceflight actually gotten more reliable and more commercial over time, or does it just look that way?** Every notebook exists to test a specific claim against the historical record — using Chi-square tests, Welch's t-tests, and rolling trend analysis rather than eyeballing charts. The pipeline itself reflects how I'd want to work on a real team: a validated PostgreSQL warehouse sits behind every notebook, so the analysis is reproducible and the data quality is checked before a single chart gets made.

---

## 📌 Project Status

| Phase | Status |
|---|---|
| ETL & PostgreSQL Warehouse | ✅ Complete |
| Data Quality Audit | ✅ Complete |
| Exploratory Data Analysis | ✅ Complete |
| Historical / Era Analysis | ✅ Complete |
| Power BI Report | 🔄 In Progress |

---

## 📂 Dataset

| Property | Detail |
|---|---|
| Source | [Kaggle](https://www.kaggle.com/datasets/maulikgajera/global-space-missions-dataset-19502025) |
| Coverage | 1957–2035 |
| Rows | ~7000 missions after cleaning and validation |
| Columns | 26 |

### Dataset Columns

| Column | Type | Description |
|---|---|---|
| `mission_id` | String | Unique mission identifier |
| `mission_name` | String | Official mission name |
| `program_type` | String | Mission program type (Robotic, Human Spaceflight, Satellite) |
| `mission_category` | String | High-level category (Moon, Mars, Earth Orbit, etc.) |
| `sub_category` | String | Specific mission type (Orbiter, Lander, Rover, CubeSat) |
| `destination` | String | Target destination or operational region |
| `status` | String | Mission status (Success, Failed, Partial Success, Ongoing, Upcoming) |
| `mission_phase` | String | Temporal classification (Past, Ongoing, Future) |
| `crew_type` | String | Crewed or Uncrewed |
| `data_returned` | String | Whether scientific or operational data was returned |
| `failure_reason` | String | Failure description for unsuccessful missions |
| `cost_usd_billion` | Float | Mission cost in billions of USD |
| `duration_days` | Float | Mission duration in days |
| `agency_name` | String | Responsible space agency |
| `country_region` | String | Country or region associated with the mission |
| `agency_type` | String | Government or Private |
| `launch_vehicle` | String | Launch vehicle used |
| `launch_site` | String | Launch facility or spaceport |
| `launch_date` | Date | Mission launch date |
| `launch_year` | Integer | Year extracted from launch date |
| `launch_decade` | String | Launch decade (e.g. 1960s, 2000s) |
| `end_date` | Date | Mission end date (NULL for ongoing/future missions) |
| `end_year` | Integer | Year extracted from end date |
| `end_decade` | String | End decade |
| `objective` | String | Primary mission objective |
| `key_achievement` | String | Major accomplishment or milestone |
| `mission_outcome_detail` | String | Detailed outcome description |
| `reference_url` | String | Source URL used for verification |

---

## 🧱 Project Architecture

This project is built as a real analytics pipeline rather than a single notebook: raw data is cleaned and validated in Python, transformed into a star-schema structure, loaded into PostgreSQL, and queried directly from the warehouse for every downstream notebook.

The pipeline separates concerns deliberately:

- Raw data ingestion
- Data cleaning and validation
- Schema transformation
- Database loading
- Analytical querying (every notebook reads from PostgreSQL, not the raw CSV)

### 📁 Repository Structure

```text
space_mission_analysis/
│
├── data/
│   └── raw/
│       └── space_missions.csv
│
├── notebooks/
│   ├── 01_data_quality_audit.ipynb
│   ├── 02_eda.ipynb
│   └── 03_historical_analysis.ipynb
│
├── src/
│   ├── config.py
│   ├── db.py
│   └── logger.py
│
├── etl_load.py
├── schema.sql
├── requirements.txt
├── .env
└── README.md
```

---

## 🗄️ Database Design

The dataset is transformed into a **star schema PostgreSQL warehouse**, designed for analytical queries and direct Power BI integration.

```
                    ┌─────────────────┐
                    │    dim_date     │
                    └────────┬────────┘
                             │
┌────────────────┐   ┌───────┴──────────┐   ┌─────────────────┐
│  dim_agency    │───│  fact_missions   │───│  dim_launch     │
└────────────────┘   └───────┬──────────┘   └─────────────────┘
                             │
                     ┌───────┴───────────┐
                     │ dim_mission_meta  │
                     └───────────────────┘
```

### Tables Overview

| Table | Rows (approx.) | Purpose |
|---|---|---|
| `fact_missions` | ~4,630 | Core mission facts |
| `dim_date` | ~7,648 | Calendar dimension |
| `dim_agency` | ~11 | Agency information |
| `dim_launch` | ~121 | Launch vehicles & sites |
| `dim_mission_meta` | ~4,630 | Mission descriptions |
| `bridge_crew` | varies | Crew member bridge table |
| `bridge_partners` | varies | Partner agency bridge table |

---

## ⚙️ ETL Pipeline (`etl_load.py`)

1. Load raw CSV
2. Clean & standardise columns
3. Parse duration text into numeric days (`duration_days`)
4. Validate data integrity rules (e.g. launch date vs. agency founding year)
5. Build dimension tables (`dim_date`, `dim_agency`, `dim_launch`, `dim_mission_meta`)
6. Build fact table (`fact_missions`)
7. Build bridge tables (`bridge_crew`, `bridge_partners`)
8. Load all tables into PostgreSQL with FK-safe ordering and indexing

---

## 🧹 Key Data Cleaning Decisions

| Issue | Action |
|---|---|
| Sentinel strings (`n/a`, `none`, etc.) | Converted to NULL |
| Duration text values (e.g. "3.9 years") | Parsed into `duration_days` |
| Cost in millions | Converted to billions |
| Launch date before agency founding year | Removed during validation |
| Date parsing mismatch (DD/MM/YYYY) | Fixed with `dayfirst=True`, resolved ~3,000 null dates |
| Structural nulls (e.g. no end date for ongoing missions) | Preserved intentionally |
| Duplicate missions | Retained as valid distinct entries |

---

## 📓 Notebooks

| Notebook | What it covers |
|---|---|
| `01_data_quality_audit.ipynb` | Post-ETL data quality checks — completeness, consistency, referential integrity against the PostgreSQL warehouse |
| `02_eda.ipynb` | Full exploratory analysis with statistical testing — Chi-square independence tests, Welch's t-tests for unequal variances, Pearson correlation |
| `03_historical_analysis.ipynb` | Era-based historical analysis: annotated timeline, 5-year rolling success rates, government vs. private sector shift, agency dominance heatmap by era, cost trends over time, mission category shifts by decade |

Every notebook queries the PostgreSQL warehouse directly via `src/db.py` (`load_missions_full()`), not the raw CSV — this keeps analysis consistent with the cleaned, validated data model.

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
scipy
jupyter
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Quickstart

### 1. Setup environment

```bash
git clone https://github.com/your-username/space-mission-analysis.git
cd space-mission-analysis
python -m venv venv
```

**Activate environment**

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure database

Create a `.env` file:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=space_missions
DB_USER=your_user
DB_PASSWORD=your_password
```

### 3. Create schema

```bash
psql -U your_user -d space_missions -f schema.sql
```

### 4. Run ETL pipeline

```bash
python -m etl_load
```

### 5. Open notebooks

```bash
jupyter notebook notebooks/
```

---

## 📊 Tech Stack

| Layer | Technology |
|---|---|
| Data Storage | PostgreSQL |
| ETL & Analysis | Python, pandas, SQLAlchemy |
| Statistical Testing | scipy.stats |
| Visualization | matplotlib, seaborn |
| BI Reporting | Power BI |
| Version Control | Git & GitHub |

---

## 📁 Key Files

| File | Purpose |
|---|---|
| `schema.sql` | Database schema + views |
| `etl_load.py` | ETL pipeline |
| `src/db.py` | Database connection and query utilities |
| `src/logger.py` | Centralised logging system |
| `src/config.py` | Configuration and path management |

---

## 👤 Author

Project by Ahmed Mohi — Data Analytics Portfolio Project