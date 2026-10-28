import duckdb

csv_path = r"F:\OneDrive\Desktop\Cyclistic\Data"

# ============================================================
# 1. Load all rides
# ============================================================
result = duckdb.sql(f"""
WITH all_rides AS (

    SELECT *
    FROM read_csv(
        '{csv_path}\\*.csv',
        union_by_name = true,
        sample_size = -1
    )
),

-- ============================================================
-- 2. Collect known station observations
-- ============================================================
station_observations AS (

    SELECT
        start_station_id AS station_id,
        start_station_name AS station_name,
        start_lat AS lat,
        start_lng AS lng
    FROM all_rides
    WHERE start_station_id IS NOT NULL
      AND start_station_name IS NOT NULL
      AND start_lat IS NOT NULL
      AND start_lng IS NOT NULL

    UNION ALL

    SELECT
        end_station_id AS station_id,
        end_station_name AS station_name,
        end_lat AS lat,
        end_lng AS lng
    FROM all_rides
    WHERE end_station_id IS NOT NULL
      AND end_station_name IS NOT NULL
      AND end_lat IS NOT NULL
      AND end_lng IS NOT NULL
),

-- ============================================================
-- 3. Count coordinate occurrences for each station ID
--    This lets us choose the most frequently observed
--    coordinate for each station.
-- ============================================================
station_coordinates AS (

    SELECT
        station_id,
        station_name,
        lat,
        lng,
        COUNT(*) AS observation_count
    FROM station_observations
    GROUP BY
        station_id,
        station_name,
        lat,
        lng
),

-- ============================================================
-- 4. Keep the most frequently observed coordinate
--    for each station ID
-- ============================================================
unique_stations_ranked AS (

    SELECT
        station_id,
        station_name,
        lat,
        lng,
        observation_count,

        ROW_NUMBER() OVER (
            PARTITION BY station_id
            ORDER BY observation_count DESC
        ) AS rn

    FROM station_coordinates
),

unique_stations AS (

    SELECT
        station_id,
        station_name,
        lat,
        lng,
        observation_count
    FROM unique_stations_ranked
    WHERE rn = 1
),

-- ============================================================
-- 5. Compare every station with every other station
-- ============================================================
station_distances AS (

    SELECT
        a.station_id AS station_id,
        a.station_name AS station_name,

        b.station_id AS nearest_candidate_id,
        b.station_name AS nearest_candidate_name,

        111320 * SQRT(
            POWER(a.lat - b.lat, 2)
            +
            POWER(
                (a.lng - b.lng)
                * COS(RADIANS(a.lat)),
                2
            )
        ) AS distance_m

    FROM unique_stations a
    CROSS JOIN unique_stations b

    WHERE a.station_id <> b.station_id
),

-- ============================================================
-- 6. Keep only the nearest station for each station
-- ============================================================
nearest_station AS (

    SELECT
        station_id,
        station_name,
        nearest_candidate_id,
        nearest_candidate_name,
        distance_m,

        ROW_NUMBER() OVER (
            PARTITION BY station_id
            ORDER BY distance_m
        ) AS rn

    FROM station_distances
),

nearest_station_only AS (

    SELECT
        station_id,
        station_name,
        nearest_candidate_id AS nearest_station_id,
        nearest_candidate_name AS nearest_station_name,
        distance_m
    FROM nearest_station
    WHERE rn = 1
)

-- ============================================================
-- 7. Final statistical summary
-- ============================================================
SELECT

    COUNT(*) AS station_count,

    ROUND(MIN(distance_m), 1) AS min_distance_m,

    ROUND(
        quantile_cont(distance_m, 0.25),
        1
    ) AS p25_distance_m,

    ROUND(
        quantile_cont(distance_m, 0.50),
        1
    ) AS median_distance_m,

    ROUND(
        quantile_cont(distance_m, 0.75),
        1
    ) AS p75_distance_m,

    ROUND(
        quantile_cont(distance_m, 0.90),
        1
    ) AS p90_distance_m,

    ROUND(
        quantile_cont(distance_m, 0.95),
        1
    ) AS p95_distance_m,

    ROUND(
        AVG(distance_m),
        1
    ) AS avg_distance_m,

    ROUND(
        MAX(distance_m),
        1
    ) AS max_distance_m

FROM nearest_station_only
""")

output_path = r"F:\OneDrive\Desktop\Cyclistic\cyclistic_station_nearest_distance_stats_v02.csv"

result.write_csv(output_path)

print(f"Saved to: {output_path}")
print(result)