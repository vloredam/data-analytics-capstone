import duckdb

sql_path = r"F:\OneDrive\Desktop\Cyclistic\Data"

output_distribution = r"F:\OneDrive\Desktop\Cyclistic\cyclistic_station_coordinate_distance_distribution_v01.csv"
output_samples = r"F:\OneDrive\Desktop\Cyclistic\cyclistic_station_coordinate_distance_samples_v01.csv"

print("--- Starting Station Coordinate Distance Diagnostic ---")

result = duckdb.sql(f"""

WITH raw AS (

    SELECT
        start_station_id,
        start_station_name,
        start_lat,
        start_lng,

        end_station_id,
        end_station_name,
        end_lat,
        end_lng

    FROM read_csv_auto(
        '{sql_path}\\*.csv',
        union_by_name = true
    )
),


-- ---------------------------------------------------------
-- Build station reference
-- One canonical coordinate per station_id
-- ---------------------------------------------------------

station_source AS (

    SELECT
        start_station_id AS station_id,
        start_lat AS lat,
        start_lng AS lng
    FROM raw

    UNION ALL

    SELECT
        end_station_id AS station_id,
        end_lat AS lat,
        end_lng AS lng
    FROM raw
),


station_candidates AS (

    SELECT
        station_id,
        lat,
        lng,
        COUNT(*) AS observations

    FROM station_source

    WHERE
        station_id IS NOT NULL
        AND lat IS NOT NULL
        AND lng IS NOT NULL

    GROUP BY
        station_id,
        lat,
        lng
),


station_reference AS (

    SELECT
        station_id,
        lat,
        lng,

        FLOOR(lat * 1000) AS lat_grid,
        FLOOR(lng * 1000) AS lng_grid

    FROM station_candidates

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY station_id
        ORDER BY observations DESC
    ) = 1
),


-- ---------------------------------------------------------
-- Missing station coordinates
-- Keep only unique coordinates to reduce workload
-- ---------------------------------------------------------

missing_source AS (

    SELECT
        'start' AS station_role,
        start_lat AS lat,
        start_lng AS lng

    FROM raw

    WHERE
        start_station_id IS NULL
        AND start_lat IS NOT NULL
        AND start_lng IS NOT NULL


    UNION ALL


    SELECT
        'end' AS station_role,
        end_lat AS lat,
        end_lng AS lng

    FROM raw

    WHERE
        end_station_id IS NULL
        AND end_lat IS NOT NULL
        AND end_lng IS NOT NULL
),


missing_coordinates AS (

    SELECT
        station_role,
        lat,
        lng,

        FLOOR(lat * 1000) AS lat_grid,
        FLOOR(lng * 1000) AS lng_grid,

        COUNT(*) AS ride_count

    FROM missing_source

    GROUP BY
        station_role,
        lat,
        lng
),


-- ---------------------------------------------------------
-- Find nearby station candidates
-- Search surrounding grid cells
-- ---------------------------------------------------------

candidate_distances AS (

    SELECT

        m.station_role,
        m.lat,
        m.lng,
        m.ride_count,

        s.station_id,
        s.lat AS station_lat,
        s.lng AS station_lng,

        -- Haversine distance in meters

        6371000 *

        2 * ASIN(

            SQRT(

                POWER(
                    SIN(
                        RADIANS(s.lat - m.lat) / 2
                    ),
                    2
                )

                +

                COS(RADIANS(m.lat))
                *
                COS(RADIANS(s.lat))

                *

                POWER(
                    SIN(
                        RADIANS(s.lng - m.lng) / 2
                    ),
                    2
                )
            )
        ) AS distance_meters

    FROM missing_coordinates m

    JOIN station_reference s

        ON ABS(s.lat_grid - m.lat_grid) <= 1
       AND ABS(s.lng_grid - m.lng_grid) <= 1
),


-- ---------------------------------------------------------
-- Nearest station for each missing coordinate
-- ---------------------------------------------------------

nearest_station AS (

    SELECT

        station_role,
        lat,
        lng,
        ride_count,
        station_id,
        station_lat,
        station_lng,
        distance_meters

    FROM candidate_distances

    QUALIFY ROW_NUMBER() OVER (

        PARTITION BY
            station_role,
            lat,
            lng

        ORDER BY
            distance_meters

    ) = 1
),


-- ---------------------------------------------------------
-- Distance distribution
-- Weighted by number of rides represented by each
-- coordinate
-- ---------------------------------------------------------

distribution AS (

    SELECT

        station_role,

        SUM(ride_count) AS total_missing_with_coordinates,

        SUM(
            CASE
                WHEN distance_meters <= 10
                THEN ride_count
                ELSE 0
            END
        ) AS within_10m,

        SUM(
            CASE
                WHEN distance_meters <= 25
                THEN ride_count
                ELSE 0
            END
        ) AS within_25m,

        SUM(
            CASE
                WHEN distance_meters <= 50
                THEN ride_count
                ELSE 0
            END
        ) AS within_50m,

        SUM(
            CASE
                WHEN distance_meters <= 100
                THEN ride_count
                ELSE 0
            END
        ) AS within_100m,

        SUM(
            CASE
                WHEN distance_meters <= 200
                THEN ride_count
                ELSE 0
            END
        ) AS within_200m,

        SUM(
            CASE
                WHEN distance_meters <= 300
                THEN ride_count
                ELSE 0
            END
        ) AS within_300m,

        SUM(
            CASE
                WHEN distance_meters > 300
                THEN ride_count
                ELSE 0
            END
        ) AS over_300m

    FROM nearest_station

    GROUP BY
        station_role
)


SELECT

    station_role,
    total_missing_with_coordinates,

    within_10m,
    ROUND(
        100.0 * within_10m
        / total_missing_with_coordinates,
        2
    ) AS pct_within_10m,

    within_25m,
    ROUND(
        100.0 * within_25m
        / total_missing_with_coordinates,
        2
    ) AS pct_within_25m,

    within_50m,
    ROUND(
        100.0 * within_50m
        / total_missing_with_coordinates,
        2
    ) AS pct_within_50m,

    within_100m,
    ROUND(
        100.0 * within_100m
        / total_missing_with_coordinates,
        2
    ) AS pct_within_100m,

    within_200m,
    ROUND(
        100.0 * within_200m
        / total_missing_with_coordinates,
        2
    ) AS pct_within_200m,

    within_300m,
    ROUND(
        100.0 * within_300m
        / total_missing_with_coordinates,
        2
    ) AS pct_within_300m,

    over_300m,
    ROUND(
        100.0 * over_300m
        / total_missing_with_coordinates,
        2
    ) AS pct_over_300m

FROM distribution

ORDER BY
    station_role;

""")

result.write_csv(output_distribution)

print(result)

print()
print(f"Distribution saved to: {output_distribution}")


# ---------------------------------------------------------
# Sample of nearest-station matches
# ---------------------------------------------------------

samples = duckdb.sql(f"""

WITH raw AS (

    SELECT
        start_station_id,
        start_lat,
        start_lng,
        end_station_id,
        end_lat,
        end_lng

    FROM read_csv_auto(
        '{sql_path}\\*.csv',
        union_by_name = true
    )
),


stations AS (

    SELECT DISTINCT
        start_station_id AS station_id,
        start_lat AS lat,
        start_lng AS lng

    FROM raw

    WHERE
        start_station_id IS NOT NULL
        AND start_lat IS NOT NULL
        AND start_lng IS NOT NULL

    UNION

    SELECT DISTINCT
        end_station_id,
        end_lat,
        end_lng

    FROM raw

    WHERE
        end_station_id IS NOT NULL
        AND end_lat IS NOT NULL
        AND end_lng IS NOT NULL
),


missing AS (

    SELECT DISTINCT
        'start' AS station_role,
        start_lat AS lat,
        start_lng AS lng

    FROM raw

    WHERE
        start_station_id IS NULL
        AND start_lat IS NOT NULL
        AND start_lng IS NOT NULL

    UNION

    SELECT DISTINCT
        'end',
        end_lat,
        end_lng

    FROM raw

    WHERE
        end_station_id IS NULL
        AND end_lat IS NOT NULL
        AND end_lng IS NOT NULL
),


candidates AS (

    SELECT

        m.station_role,
        m.lat,
        m.lng,
        s.station_id,
        s.lat AS station_lat,
        s.lng AS station_lng,

        6371000 *

        2 * ASIN(

            SQRT(

                POWER(
                    SIN(
                        RADIANS(s.lat - m.lat) / 2
                    ),
                    2
                )

                +

                COS(RADIANS(m.lat))
                *
                COS(RADIANS(s.lat))
                *

                POWER(
                    SIN(
                        RADIANS(s.lng - m.lng) / 2
                    ),
                    2
                )
            )
        ) AS distance_meters

    FROM missing m

    JOIN stations s

        ON ABS(FLOOR(s.lat * 1000) - FLOOR(m.lat * 1000)) <= 1
       AND ABS(FLOOR(s.lng * 1000) - FLOOR(m.lng * 1000)) <= 1
),


nearest AS (

    SELECT *

    FROM candidates

    QUALIFY ROW_NUMBER() OVER (

        PARTITION BY
            station_role,
            lat,
            lng

        ORDER BY
            distance_meters

    ) = 1
)


SELECT *

FROM nearest

ORDER BY
    station_role,
    distance_meters

LIMIT 1000;

""")

samples.write_csv(output_samples)

print(f"Samples saved to: {output_samples}")

print("--- Ending Station Coordinate Distance Diagnostic ---")