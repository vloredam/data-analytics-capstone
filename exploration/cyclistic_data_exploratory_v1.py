import os
import glob
import duckdb

sql_path = r"F:\OneDrive\Desktop\Cyclist\Data"
csv_file = glob.glob(f"{sql_path}\\*.csv")

print ("---  Starting Cyclistic CSV Analyzer v0.1  ---- ")
for file in csv_file:
    csv_path = file
    print(os.path.basename(file), " result: ")
    
    result = duckdb.sql(f"""
        SELECT
        member_casual,
        COUNT(
            CASE
                WHEN ended_at - started_at < INTERVAL '1 minute'
                THEN 1
                ELSE NULL
            END
        ) AS "0-1",
        COUNT(
            CASE
                WHEN ended_at - started_at < INTERVAL '2 minute'
                THEN 1
                ELSE NULL
            END
        ) AS "0-2",
        COUNT(
            CASE
                WHEN ended_at - started_at < INTERVAL '5 minute'
                THEN 1
                ELSE NULL
            END
        ) AS "0-5",
        COUNT(
            CASE
                WHEN ended_at - started_at < INTERVAL '10 minute'
                THEN 1
                ELSE NULL
            END
        ) AS "0-10",
        COUNT(
            CASE
                WHEN ended_at - started_at < INTERVAL '30 minute'
                THEN 1
                ELSE NULL
            END
        ) AS "0-30",
        COUNT(
            CASE
                WHEN ended_at - started_at < INTERVAL '60 minute'
                THEN 1
                ELSE NULL
            END
        ) AS "0-60",
        COUNT(
            CASE
                WHEN ended_at - started_at >= INTERVAL '60 minute'
                AND ended_at - started_at < INTERVAL '120 minute'
                THEN 1
                ELSE NULL
            END
        ) AS "60-120"
        
    FROM read_csv_auto('{csv_path}')
    WHERE ended_at > started_at
    GROUP BY member_casual
    ORDER BY member_casual;
    """)

    print(result.fetchall(), "\n\n")

print ("---  Ending Cyclistic CSV Analyzer v0.1  ---- ")




