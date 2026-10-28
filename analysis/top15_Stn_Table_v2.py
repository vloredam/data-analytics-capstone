from pathlib import Path

import duckdb


# Project directories
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"
EXPLORATION_DIR = REPO_ROOT / "exploration"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
EXPLORATION_DIR.mkdir(parents=True, exist_ok=True)

TOP15_PATH = RESULTS_DIR / "cyclistic_top15_stations_by_customer.csv"
UNKNOWN_PATH = EXPLORATION_DIR / "cyclistic_unknown_station_candidates_monthly_v01.csv"
POTENTIAL_PATH = EXPLORATION_DIR / "cyclistic_top15_stations_with_unknown_potential.csv"

con = duckdb.connect()


# ============================================================
# 1. Build Top 15 stations by customer type
#    Ranking = identified START + identified END rides
# ============================================================

top15 = con.sql(f"""
WITH all_rides AS (

    SELECT *
    FROM read_csv(
        '{DATA_DIR.as_posix()}/*.csv',
        union_by_name = true,
        sample_size = -1
    )
),

station_activity AS (

    SELECT
        member_casual,
        start_station_id AS station_id,
        start_station_name AS station_name,
        COUNT(*) AS start_rides,
        0 AS end_rides
    FROM all_rides
    WHERE start_station_id IS NOT NULL
      AND start_station_name IS NOT NULL
    GROUP BY
        member_casual,
        start_station_id,
        start_station_name

    UNION ALL

    SELECT
        member_casual,
        end_station_id AS station_id,
        end_station_name AS station_name,
        0 AS start_rides,
        COUNT(*) AS end_rides
    FROM all_rides
    WHERE end_station_id IS NOT NULL
      AND end_station_name IS NOT NULL
    GROUP BY
        member_casual,
        end_station_id,
        end_station_name
),

station_totals AS (

    SELECT
        member_casual,
        station_id,
        station_name,
        SUM(start_rides) AS start_rides,
        SUM(end_rides) AS end_rides,
        SUM(start_rides + end_rides) AS total_rides
    FROM station_activity
    GROUP BY
        member_casual,
        station_id,
        station_name
),

ranked AS (

    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY member_casual
            ORDER BY total_rides DESC
        ) AS rank
    FROM station_totals
)

SELECT
    member_casual,
    rank,
    station_id,
    station_name,
    start_rides,
    end_rides,
    total_rides
FROM ranked
WHERE rank <= 15
ORDER BY
    member_casual,
    rank
""").df()

top15.to_csv(TOP15_PATH, index=False)
print(f"Saved: {TOP15_PATH}")
print(top15)

# ============================================================
# 2. Add UNKNOWN rides within <50m
# ============================================================

top15_potential = con.sql(f"""
WITH top15 AS (

    SELECT *
    FROM read_csv_auto('{TOP15_PATH.as_posix()}')
),

unknowns AS (

    SELECT *
    FROM read_csv_auto('{UNKNOWN_PATH.as_posix()}')
    WHERE distance_m < 50
),

unknown_agg AS (

    SELECT
        member_casual,
        nearest_station_id AS station_id,
        nearest_station_name AS station_name,

        SUM(
            CASE
                WHEN station_role = 'start'
                THEN ride_count
                ELSE 0
            END
        ) AS unknown_start_rides,

        SUM(
            CASE
                WHEN station_role = 'end'
                THEN ride_count
                ELSE 0
            END
        ) AS unknown_end_rides,

        SUM(ride_count) AS unknown_total_rides
    FROM unknowns
    GROUP BY
        member_casual,
        nearest_station_id,
        nearest_station_name
),

combined AS (

    SELECT
        t.member_casual,
        t.rank,
        t.station_id,
        t.station_name,

        t.start_rides AS identified_start_rides,
        COALESCE(u.unknown_start_rides, 0)
            AS unknown_start_rides,
        t.start_rides
        + COALESCE(u.unknown_start_rides, 0)
            AS potential_start_rides,

        t.end_rides AS identified_end_rides,
        COALESCE(u.unknown_end_rides, 0)
            AS unknown_end_rides,
        t.end_rides
        + COALESCE(u.unknown_end_rides, 0)
            AS potential_end_rides,

        t.total_rides AS identified_total_rides,
        COALESCE(u.unknown_total_rides, 0)
            AS unknown_total_rides,
        t.total_rides
        + COALESCE(u.unknown_total_rides, 0)
            AS potential_total_rides
    FROM top15 t
    LEFT JOIN unknown_agg u
        ON t.member_casual = u.member_casual
       AND t.station_id = u.station_id
)

SELECT *
FROM combined
ORDER BY
    member_casual,
    rank
""").df()

top15_potential.to_csv(POTENTIAL_PATH, index=False)
print(f"Saved: {POTENTIAL_PATH}")
print(top15_potential)

con.close()
