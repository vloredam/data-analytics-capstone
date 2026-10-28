from pathlib import Path
import duckdb
from openpyxl import Workbook

# Project directories: raw CSV files stay local and are not committed to GitHub.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_FILE = PROJECT_ROOT / "results" / "Cyclistic_Results.xlsx"


def validate_results(file_path, query_result):
    """Compare the number of valid rides with the number of classified rides."""
    data = query_result.fetchall()
    classified_total = sum(row[3] for row in data)

    valid_total = duckdb.sql(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{file_path.as_posix()}')
        WHERE ended_at > started_at
        """
    ).fetchone()[0]

    return valid_total, classified_total, data


def autosize_columns(worksheet):
    """Adjust worksheet column widths to fit the cell contents."""
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter

        for cell in column:
            if cell.value is not None:
                max_length = max(max_length, len(str(cell.value)))

        worksheet.column_dimensions[column_letter].width = max_length + 2


# Find all monthly CSV files in the local data directory.
csv_files = sorted(DATA_DIR.glob("*.csv"))

if not csv_files:
    raise FileNotFoundError(f"No CSV files found in: {DATA_DIR}")

# Create the Excel workbook and remove the default worksheet.
workbook = Workbook()
workbook.remove(workbook.active)

print("--- Starting Cyclistic Ride Duration Interval Analysis ---")

for file_path in csv_files:
    outcome_name = file_path.stem
    print(f"Processing: {outcome_name}")

    result = duckdb.sql(
        f"""
        SELECT
            member_casual,
            rideable_type,
            duration_interval,
            COUNT(*) AS ride_count
        FROM (
            SELECT
                member_casual,
                rideable_type,
                CASE
                    WHEN ended_at - started_at < INTERVAL '10 minute' THEN '0-10'
                    WHEN ended_at - started_at < INTERVAL '20 minute' THEN '10-20'
                    WHEN ended_at - started_at < INTERVAL '30 minute' THEN '20-30'
                    WHEN ended_at - started_at < INTERVAL '40 minute' THEN '30-40'
                    WHEN ended_at - started_at < INTERVAL '50 minute' THEN '40-50'
                    WHEN ended_at - started_at < INTERVAL '60 minute' THEN '50-60'
                    WHEN ended_at - started_at < INTERVAL '120 minute' THEN '60-120'
                    ELSE '120+'
                END AS duration_interval
            FROM read_csv_auto('{file_path.as_posix()}')
            WHERE ended_at > started_at
        )
        GROUP BY member_casual, rideable_type, duration_interval
        ORDER BY member_casual, rideable_type, duration_interval;
        """
    )

    valid_total, classified_total, data = validate_results(file_path, result)

    # Excel limits worksheet names to 31 characters.
    worksheet = workbook.create_sheet(title=outcome_name[:31])

    # Add the table headers.
    headers = [
        "member_casual",
        "rideable_type",
        "duration_interval",
        "ride_count",
    ]
    worksheet.append(headers)

    # Add the aggregated results.
    for row in data:
        worksheet.append(row)

    # Add validation results below the table.
    worksheet.append([])
    worksheet.append(["Valid rides", valid_total])
    worksheet.append(["Classified rides", classified_total])
    worksheet.append(["Status", "PASS" if valid_total == classified_total else "FAIL"])

    autosize_columns(worksheet)

    print(f"  Valid rides: {valid_total}")
    print(f"  Classified rides: {classified_total}")
    print(f"  Status: {'PASS' if valid_total == classified_total else 'FAIL'}")

# Create the results directory if it does not already exist.
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Save the Excel workbook.
workbook.save(OUTPUT_FILE)

print(f"Excel file created successfully: {OUTPUT_FILE}")
print("--- Analysis complete ---")