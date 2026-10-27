from pathlib import Path

import duckdb


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CSV_PATTERN = (DATA_DIR / "*.csv").as_posix()


result = duckdb.sql(f"""
WITH rides AS (

    SELECT
        ride_id,
        started_at,
        ended_at,
        start_station_id,
        start_station_name,
        end_station_id,
        end_station_name
    FROM read_csv(
        '{CSV_PATTERN}',
        union_by_name = true,
        sample_size = -1
    )
    WHERE ended_at >= started_at
),

unknown_rides AS (

    SELECT
        ride_id
    FROM rides
    WHERE
        (start_station_id IS NULL AND start_station_name IS NULL)
        OR
        (end_station_id IS NULL AND end_station_name IS NULL)

    -- Count each ride only once, even when both stations are unknown
    GROUP BY ride_id
)

SELECT
    COUNT(*) AS rides_with_at_least_one_unknown_station,

    (SELECT COUNT(*) FROM rides) AS total_valid_rides,

    ROUND(
        100.0 * COUNT(*)
        / (SELECT COUNT(*) FROM rides),
        2
    ) AS percentage_of_valid_rides

FROM unknown_rides
""")

print(result)