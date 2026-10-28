# Cyclistic Bike-Share Analysis

A data analysis project exploring how Cyclistic's annual members and casual riders use the bike-share system differently, with the goal of informing membership-conversion strategies.


## Project Context

Cyclistic is a fictional bike-share company in Chicago. The case study places the analyst on Cyclistic's marketing analytics team, where the business goal is to increase annual memberships. Because annual members are considered more profitable than casual riders, the marketing team wants to understand behavioural differences between the two groups and use these insights to inform strategies for converting casual riders into members.


## Business Question

How do annual members and casual riders use Cyclistic bikes differently?


## Approach

This project analyzed more than 6 million bike rides over a 12-month period, from August 2025 to July 2026. Python and SQL (DuckDB) were used for data validation, preparation, aggregation, and analysis, while Microsoft Excel was used for supplementary analysis, results review, and visualization.


## Highlights

- High-volume stations differ between annual members and casual riders.
- Ridership shows strong seasonality, with casual riders exhibiting greater seasonal variation than members.
- Casual riders tend to take longer rides, particularly when using classic bikes.


## Recommendations

- Target high-volume casual-use locations during the high-demand season.
- Leverage the strong adoption of electric bikes in membership-focused strategies.


## Key Limitation

The primary limitation of this analysis is that the dataset does not provide user-level information. As a result, the analysis cannot measure individual usage patterns, identify specific casual riders with higher conversion potential, or directly evaluate membership conversion.

The station analysis was also limited by incomplete station identification in the source data, which affects the completeness of the observed spatial patterns.

Finally, the 12-month study period provides useful insights into seasonal variation but limits the ability to identify recurring seasonal patterns or year-over-year trends. A longer observation period would provide a stronger basis for evaluating changes over time.


## Repository

- `analysis/` — Python scripts used for the final analysis.
- `exploration/` — Exploratory analyses, intermediate work, and diagnostic outputs.
- `results/` — Aggregated datasets and analysis outputs used to support the findings.
- `report/` — Final project report.


## Full Report

[Final project report](https://github.com/vloredam/data-analytics-capstone/tree/main/report/cyclistic_capstone_report.pdf)


## Tools

Python · SQL (DuckDB) · Microsoft Excel


## AI-Assisted Development

AI-assisted coding tools were used during the development of portions of this analysis. They were used as a learning, problem-solving, and productivity aid. Analytical decisions, methodology, validation, interpretation, and final conclusions were reviewed and determined by the author.


## About the Case Study

This project was developed as part of the Google Data Analytics Professional Certificate capstone case study.
