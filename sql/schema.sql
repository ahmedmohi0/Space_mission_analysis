
DROP TABLE IF EXISTS bridge_crew          CASCADE;
DROP TABLE IF EXISTS bridge_partners      CASCADE;
DROP TABLE IF EXISTS fact_missions        CASCADE;
DROP TABLE IF EXISTS dim_mission_meta     CASCADE;
DROP TABLE IF EXISTS dim_agency           CASCADE;
DROP TABLE IF EXISTS dim_launch           CASCADE;
DROP TABLE IF EXISTS dim_date             CASCADE;

CREATE TABLE dim_date (
    date_id       SERIAL        PRIMARY KEY,
    full_date     DATE          NOT NULL UNIQUE,
    year          SMALLINT      NOT NULL,
    quarter       SMALLINT      NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month         SMALLINT      NOT NULL CHECK (month   BETWEEN 1 AND 12),
    month_name    VARCHAR(10)   NOT NULL,
    week          SMALLINT      NOT NULL,
    day           SMALLINT      NOT NULL,
    decade        VARCHAR(10)   NOT NULL   
);

CREATE TABLE dim_agency (
    agency_id       SERIAL       PRIMARY KEY,
    agency_name     VARCHAR(255) NOT NULL,
    country_region  VARCHAR(255),
    agency_type     VARCHAR(50)            
);

CREATE TABLE dim_launch (
    launch_id       SERIAL       PRIMARY KEY,
    launch_vehicle  VARCHAR(255),
    launch_site     VARCHAR(255)
);

CREATE TABLE dim_mission_meta (
    mission_id            VARCHAR(20)  PRIMARY KEY,  
    mission_name          VARCHAR(500),
    objective             TEXT,
    key_achievement       TEXT,
    mission_outcome_detail TEXT,
    reference_url         TEXT
);

CREATE TABLE fact_missions (
    mission_id          VARCHAR(20)     PRIMARY KEY,

    -- Foreign keys
    agency_id           INT             REFERENCES dim_agency(agency_id),
    launch_id           INT             REFERENCES dim_launch(launch_id),
    launch_date_id      INT             REFERENCES dim_date(date_id),
    end_date_id         INT             REFERENCES dim_date(date_id),   -- NULL if ongoing/future

    -- Categoricals (kept in fact for direct Power BI slicing)
    program_type        VARCHAR(100),   -- Robotic, Human Spaceflight, Satellite…
    mission_category    VARCHAR(100),   -- Moon, Mars, Earth Orbit…
    sub_category        VARCHAR(100),   -- Orbiter, Lander, Rover, CubeSat…
    destination         VARCHAR(255),
    status              VARCHAR(50),    -- Su,ccess | Failed | Partial Success | Ongoing | Upcoming
    mission_phase       VARCHAR(20),    -- Past | Ongoing | Future
    crew_type           VARCHAR(20),    -- Crewed | Uncrewed
    data_returned       VARCHAR(20),    -- Yes | No | Partial | N/A

    -- Failure detail (NULL for non-failed missions)
    failure_reason      TEXT,

    -- Measures
    cost_usd_billion    DECIMAL(12, 2), -- NULL if unknown
    duration_days       DECIMAL(10, 2)  -- Parsed from Duration string by Python; NULL if ongoing
);

CREATE TABLE bridge_crew (
    id              SERIAL       PRIMARY KEY,
    mission_id      VARCHAR(20)  NOT NULL REFERENCES fact_missions(mission_id),
    crew_member     VARCHAR(255) NOT NULL
);

CREATE TABLE bridge_partners (
    id              SERIAL       PRIMARY KEY,
    mission_id      VARCHAR(20)  NOT NULL REFERENCES fact_missions(mission_id),
    partner_agency  VARCHAR(255) NOT NULL
);


-- INDEXES  (


CREATE INDEX idx_fact_agency        ON fact_missions(agency_id);
CREATE INDEX idx_fact_launch        ON fact_missions(launch_id);
CREATE INDEX idx_fact_launch_date   ON fact_missions(launch_date_id);
CREATE INDEX idx_fact_end_date      ON fact_missions(end_date_id);
CREATE INDEX idx_fact_status        ON fact_missions(status);
CREATE INDEX idx_fact_phase         ON fact_missions(mission_phase);
CREATE INDEX idx_fact_category      ON fact_missions(mission_category);
CREATE INDEX idx_fact_crew_type     ON fact_missions(crew_type);
CREATE INDEX idx_bridge_crew_mid    ON bridge_crew(mission_id);
CREATE INDEX idx_bridge_part_mid    ON bridge_partners(mission_id);



-- ANALYTICAL VIEWS  

-- Agency-level summary
CREATE OR REPLACE VIEW vw_agency_summary AS
SELECT
    a.agency_name,
    a.country_region,
    a.agency_type,
    COUNT(f.mission_id)                                          AS total_missions,
    SUM(CASE WHEN f.status = 'Success'         THEN 1 ELSE 0 END) AS successful_missions,
    SUM(CASE WHEN f.status = 'Failed'          THEN 1 ELSE 0 END) AS failed_missions,
    SUM(CASE WHEN f.status = 'Partial Success' THEN 1 ELSE 0 END) AS partial_missions,
    sum(CASE WHEN f.status = 'Ongoing'         THEN 1 ELSE 0 END) AS ongoing_missions,
    sum(CASE WHEN f.status = 'Upcoming'        THEN 1 ELSE 0 END) AS upcoming_missions,
    sum(CASE WHEN f.crew_type = 'Crewed'        THEN 1 ELSE 0 END) AS crewed_missions,
    ROUND(
        100.0 * SUM(CASE WHEN f.status = 'Success' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(f.mission_id), 0), 2
    )                                                            AS success_rate_pct,
    ROUND(AVG(f.cost_usd_billion), 2)                           AS avg_cost_usd_billion,
    ROUND(SUM(f.cost_usd_billion), 2)                           AS total_cost_usd_billion
FROM fact_missions  f
JOIN dim_agency     a ON f.agency_id = a.agency_id
GROUP BY a.agency_name, a.country_region, a.agency_type;


-- Yearly launch trend
CREATE OR REPLACE VIEW vw_yearly_trend AS
SELECT
    d.year,
    d.decade,
    COUNT(f.mission_id)                                          AS total_launches,
    SUM(CASE WHEN f.status    = 'Success'   THEN 1 ELSE 0 END)  AS successes,
    SUM(CASE WHEN f.status    = 'Failed'    THEN 1 ELSE 0 END)  AS failures,
    SUM(CASE WHEN f.crew_type = 'Crewed'    THEN 1 ELSE 0 END)  AS crewed_missions,
    ROUND(AVG(f.cost_usd_billion), 2)                           AS avg_cost_usd_billion
FROM fact_missions  f
JOIN dim_date       d ON f.launch_date_id = d.date_id
GROUP BY d.year, d.decade
ORDER BY d.year;


-- Destination breakdown
CREATE OR REPLACE VIEW vw_destination_summary AS
SELECT
    f.destination,
    f.mission_category,
    COUNT(f.mission_id)                                          AS total_missions,
    ROUND(
        100.0 * SUM(CASE WHEN f.status = 'Success' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(f.mission_id), 0), 2
    )                                                            AS success_rate_pct,
    ROUND(AVG(f.cost_usd_billion), 2)                           AS avg_cost_usd_billion
FROM fact_missions f
GROUP BY f.destination, f.mission_category
ORDER BY total_missions DESC;
