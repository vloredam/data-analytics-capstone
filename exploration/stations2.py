import duckdb

sql_path = r"F:\OneDrive\Desktop\Cyclistic\Data"
output_path = r"F:\OneDrive\Desktop\Cyclistic\cyclistic_station_exploration_overall_v02.csv"

print("--- Starting Cyclistic Station Explorer Overall v0.2 ---")

result = duckdb.sql(f"""
WITH rides AS (
    SELECT
        member_casual,
        ride_id,
        start_station_id,
        start_station_name,
        end_station_id,
        end_station_name
    FROM read_csv_auto(
        '{sql_path}\\*.csv',
        union_by_name = true
    )
),

station_events AS (

    SELECT
        member_casual,
        'start' AS station_role,
        start_station_id AS station_id,
        start_station_name AS station_name,
        ride_id
    FROM rides
    WHERE start_station_id IS NOT NULL
      AND start_station_name IS NOT NULL

    UNION ALL

    SELECT
        member_casual,
        'end' AS station_role,
        end_station_id AS station_id,
        end_station_name AS station_name,
        ride_id
    FROM rides
    WHERE end_station_id IS NOT NULL
      AND end_station_name IS NOT NULL
),

station_counts AS (
    SELECT
        member_casual,
        station_role,
        station_id,
        station_name,
        COUNT(*) AS ride_count
    FROM station_events
    GROUP BY
        member_casual,
        station_role,
        station_id,
        station_name
),

ranked AS (
    SELECT
        *,
        SUM(ride_count) OVER (
            PARTITION BY member_casual, station_role
        ) AS identified_station_rides,

        ROW_NUMBER() OVER (
            PARTITION BY member_casual, station_role
            ORDER BY ride_count DESC
        ) AS station_rank

    FROM station_counts
)

SELECT
    member_casual,
    station_role,
    station_rank,
    station_id,
    station_name,
    ride_count,
    identified_station_rides,
    ROUND(
        100.0 * ride_count / identified_station_rides,
        2
    ) AS share_of_identified_station_rides

FROM ranked

WHERE station_rank <= 20

ORDER BY
    member_casual,
    station_role,
    station_rank;
""")

result.write_csv(output_path)

print(result)

print(f"\nOutput saved to: {output_path}")

print("--- Ending Cyclistic Station Explorer Overall v0.2 ---")