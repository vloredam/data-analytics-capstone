import duckdb

csv_path = r"F:\OneDrive\Desktop\Cyclistic\Data"

print("--- Starting Station Coordinate Distance Diagnostic - STN Unkwn---")

result = duckdb.sql(f"""
WITH
-- ============================================================
-- 1. Base consolidada
-- ============================================================
all_rides AS (
    SELECT *
    FROM read_csv(
        '{csv_path}\\*.csv',
        union_by_name = true,
        sample_size = -1
    )
),

-- ============================================================
-- 2. UNKNOWN station events
-- ============================================================
unknown_points AS (

    -- START
    SELECT
        DATE_TRUNC('month', started_at) AS month,
        'start' AS station_role,
        member_casual,
        start_lat AS unknown_lat,
        start_lng AS unknown_lng
    FROM all_rides
    WHERE start_station_name IS NULL
      AND start_station_id IS NULL
      AND start_lat IS NOT NULL
      AND start_lng IS NOT NULL

    UNION ALL

    -- END
    SELECT
        DATE_TRUNC('month', ended_at) AS month,
        'end' AS station_role,
        member_casual,
        end_lat AS unknown_lat,
        end_lng AS unknown_lng
    FROM all_rides
    WHERE end_station_name IS NULL
      AND end_station_id IS NULL
      AND end_lat IS NOT NULL
      AND end_lng IS NOT NULL
),

-- ============================================================
-- 3. Aggregate recurring UNKNOWN coordinates by month
-- ============================================================
unknown_counts AS (
    SELECT
        month,
        station_role,
        member_casual,
        unknown_lat,
        unknown_lng,
        COUNT(*) AS ride_count
    FROM unknown_points
    GROUP BY
        month,
        station_role,
        member_casual,
        unknown_lat,
        unknown_lng
),

-- ============================================================
-- 4. Known stations
-- ============================================================
known_stations AS (

    SELECT DISTINCT
        start_station_id AS station_id,
        start_station_name AS station_name,
        start_lat AS station_lat,
        start_lng AS station_lng
    FROM all_rides
    WHERE start_station_id IS NOT NULL
      AND start_station_name IS NOT NULL
      AND start_lat IS NOT NULL
      AND start_lng IS NOT NULL

    UNION

    SELECT DISTINCT
        end_station_id AS station_id,
        end_station_name AS station_name,
        end_lat AS station_lat,
        end_lng AS station_lng
    FROM all_rides
    WHERE end_station_id IS NOT NULL
      AND end_station_name IS NOT NULL
      AND end_lat IS NOT NULL
      AND end_lng IS NOT NULL
),

-- ============================================================
-- 5. Calculate distance to all known stations
-- ============================================================
candidate_distances AS (
    SELECT
        u.month,
        u.station_role,
        u.member_casual,
        u.unknown_lat,
        u.unknown_lng,
        u.ride_count,

        k.station_id,
        k.station_name,
        k.station_lat,
        k.station_lng,

        111320 * SQRT(
            POWER(u.unknown_lat - k.station_lat, 2)
            +
            POWER(
                (u.unknown_lng - k.station_lng)
                * COS(RADIANS(u.unknown_lat)),
                2
            )
        ) AS distance_m

    FROM unknown_counts u
    CROSS JOIN known_stations k
),

-- ============================================================
-- 6. Select nearest known station
-- ============================================================
ranked_candidates AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY
                month,
                station_role,
                member_casual,
                unknown_lat,
                unknown_lng
            ORDER BY distance_m
        ) AS rn
    FROM candidate_distances
)

-- ============================================================
-- 7. Final output
-- ============================================================
SELECT
    STRFTIME(month, '%Y-%m') AS month,

    station_role,
    member_casual,

    unknown_lat,
    unknown_lng,

    ride_count,

    station_name AS nearest_station_name,
    station_id AS nearest_station_id,

    station_lat AS nearest_lat,
    station_lng AS nearest_lng,

    ROUND(distance_m, 1) AS distance_m,

    CASE
        WHEN distance_m <= 20 THEN '<=20m'
        WHEN distance_m <= 50 THEN '20-50m'
        ELSE '>50m'
    END AS distance_category

FROM ranked_candidates
WHERE rn = 1
ORDER BY
    month,
    station_role,
    ride_count DESC;
"""
)

output_path = r"F:\OneDrive\Desktop\Cyclistic\cyclistic_unknown_station_candidates_monthly_v01.csv"
result.write_csv(output_path)

print(f"Saved to: {output_path}")