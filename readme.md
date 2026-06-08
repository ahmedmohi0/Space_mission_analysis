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

| Property | Detail                                                                                        |
| -------- | --------------------------------------------------------------------------------------------- |
| Source   | [Kaggle](https://www.kaggle.com/datasets/maulikgajera/global-space-missions-dataset-19502025) |
| Coverage | 1957–2035 (78 years of space history)                                                         |
| Rows     | ~10,500 missions                                                                              |
| Columns  | 26                                                                                            |

---

### Dataset Columns

| Column                   | Type    | Description                                                          |
| ------------------------ | ------- | -------------------------------------------------------------------- |
| `mission_id`             | String  | Unique mission identifier                                            |
| `mission_name`           | String  | Official mission name                                                |
| `program_type`           | String  | Mission program type (e.g. Robotic, Human Spaceflight, Satellite)    |
| `mission_category`       | String  | High-level mission category (e.g. Moon, Mars, Earth Orbit)           |
| `sub_category`           | String  | Specific mission type (e.g. Orbiter, Lander, Rover, CubeSat)         |
| `destination`            | String  | Target destination or operational region                             |
| `status`                 | String  | Mission status (Success, Failed, Partial Success, Ongoing, Upcoming) |
| `mission_phase`          | String  | Temporal classification (Past, Ongoing, Future)                      |
| `crew_type`              | String  | Crewed or Uncrewed mission                                           |
| `data_returned`          | String  | Indicates whether scientific or operational data was returned        |
| `failure_reason`         | String  | Failure description for unsuccessful missions                        |
| `cost_usd_billion`       | Float   | Mission cost in billions of USD                                      |
| `duration_days`          | Float   | Mission duration in days                                             |
| `agency_name`            | String  | Responsible space agency or organization                             |
| `country_region`         | String  | Country or region associated with the mission                        |
| `agency_type`            | String  | Agency classification (Government or Private)                        |
| `launch_vehicle`         | String  | Launch vehicle used for the mission                                  |
| `launch_site`            | String  | Launch facility or spaceport                                         |
| `launch_date`            | Date    | Mission launch date                                                  |
| `launch_year`            | Integer | Launch year extracted from launch date                               |
| `launch_decade`          | String  | Launch decade (e.g. 1960s, 2000s, 2020s)                             |
| `end_date`               | Date    | Mission end date (NULL for ongoing or future missions)               |
| `end_year`               | Integer | End year extracted from end date                                     |
| `end_decade`             | String  | End decade (e.g. 1970s, 2010s)                                       |
| `objective`              | String  | Primary mission objective                                            |
| `key_achievement`        | String  | Major accomplishment or milestone achieved                           |
| `mission_outcome_detail` | String  | Detailed description of mission outcome                              |
| `reference_url`          | String  | Source URL used for verification                                     |

---

## 🧱 Project Architecture

This project was designed as a complete analytical pipeline rather than a standalone notebook workflow.

The dataset is first cleaned and validated in Python, transformed into an analytical star-schema structure, and then loaded into PostgreSQL using a custom ETL pipeline.

The project separates:

* Raw data ingestion
* Data cleaning and validation
* Schema transformation
* Database loading
* Analytical querying

---

### 📁 Repository Structure

```text
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
├── .env
└── README.md
```

---

## 🗄️ Database Design

The raw dataset was transformed into a **star schema PostgreSQL warehouse** optimized for analytical queries and BI integration.

### Schema Diagram

```
                    ┌─────────────────┐
                    │   dim_date      │
                    └────────┬────────┘
                             │
┌────────────────┐   ┌───────┴──────────┐   ┌─────────────────┐
│  dim_agency    │   │  fact_missions   │   │  dim_launch     │
└────────────────┘   └───────┬──────────┘   └─────────────────┘
                             │
                     ┌───────┴──────────┐
                     │ dim_mission_meta  │
                     └───────────────────┘
```

### Tables Overview

| Table              | Rows (approx.) | Purpose                 |
| ------------------ | -------------- | ----------------------- |
| `fact_missions`    | ~4,630         | Core mission facts      |
| `dim_date`         | ~7,648         | Calendar dimension      |
| `dim_agency`       | ~11            | Agency information      |
| `dim_launch`       | ~121           | Launch vehicles & sites |
| `dim_mission_meta` | ~4,630         | Mission descriptions    |

---

## ⚙️ ETL Pipeline (`etl_load.py`)

### Pipeline Steps

1. Load raw CSV
2. Clean & standardise data
3. Parse duration fields into numeric days
4. Validate data integrity rules
5. Build dimension tables
6. Build fact table
7. Create analytical views
8. Load into PostgreSQL

---

## 🧹 Key Data Cleaning Decisions

| Issue                                    | Action                             |
| ---------------------------------------- | ---------------------------------- |
| Sentinel strings (`n/a`, `none`, etc.)   | Converted to NULL                  |
| Duration text values                     | Parsed into `duration_days`        |
| Cost in millions                         | Converted to billions              |
| Invalid dates (`end_date < launch_date`) | Removed (164 records)              |
| Structural nulls                         | Preserved intentionally            |
| Duplicate missions                       | Retained (valid distinct missions) |
| Agency founding violations               | Removed during validation          |

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

**Activate environment:**

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

---

### 2. Configure database

Create `.env` file:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=space_missions
DB_USER=your_user
DB_PASSWORD=your_password
```

---

### 3. Create schema

```bash
psql -U your_user -d space_missions -f schema.sql
```

---

### 4. Run ETL pipeline

```bash
python -m etl_load
```

---

### 5. Open notebooks

```bash
jupyter notebook notebooks/
```

---

## 📊 Tech Stack

| Layer           | Technology                           |
| --------------- | ------------------------------------ |
| Data Storage    | PostgreSQL                           |
| ETL & Analysis  | Python, pandas, SQLAlchemy           |
| ML              | scikit-learn, XGBoost, SHAP, Prophet |
| Visualization   | matplotlib, seaborn                  |
| BI              | Power BI                             |
| Version Control | Git & GitHub                         |

---

## 📁 Key Files

| File                     | Purpose                    |
| ------------------------ | -------------------------- |
| `schema.sql`             | Database schema + views    |
| `etl_load.py`            | ETL pipeline               |
| `src/db.py`              | DB utilities               |
| `src/logger.py`          | Logging system             |
| `src/config.py`          | Configuration              |
| `01_data_cleaning.ipynb` | Data quality documentation |

---

## 👤 Author

Project by Ahmed Mohi  — Data Analytics Portfolio Project
