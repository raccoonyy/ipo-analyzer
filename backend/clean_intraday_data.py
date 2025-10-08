"""
Clean Intraday Data
Filter out invalid records from KIS API response
"""

import pandas as pd
from pathlib import Path

def clean_intraday_data():
    """Clean and filter intraday data"""
    print("=" * 80)
    print("CLEANING INTRADAY DATA")
    print("=" * 80)
    print()

    # Load raw intraday data
    input_file = "data/raw/intraday/ipo_intraday_2022_2024.csv"
    df = pd.read_csv(input_file)

    print(f"Loaded {len(df):,} raw records")
    print()

    # Filter valid records
    # Valid datetime_str should be 12 digits: YYYYMMDDHHMM
    df["datetime_str_len"] = df["datetime_str"].astype(str).str.len()

    print("Record breakdown by datetime_str length:")
    print(df["datetime_str_len"].value_counts().sort_index())
    print()

    # Keep only 12-digit datetime strings (valid format)
    df_valid = df[df["datetime_str_len"] == 12].copy()

    # Also filter out records with all zeros
    df_valid = df_valid[
        (df_valid["open"] > 0) |
        (df_valid["high"] > 0) |
        (df_valid["close"] > 0)
    ].copy()

    print(f"Valid records: {len(df_valid):,} ({len(df_valid)/len(df)*100:.1f}%)")
    print(f"Filtered out: {len(df) - len(df_valid):,} records")
    print()

    # Parse datetime properly
    df_valid["datetime"] = pd.to_datetime(df_valid["datetime_str"], format="%Y%m%d%H%M", errors="coerce")

    # Drop any that failed to parse
    df_valid = df_valid.dropna(subset=["datetime"])

    print(f"After datetime validation: {len(df_valid):,} records")
    print()

    # Select relevant columns
    columns_to_keep = [
        "company_name",
        "code",
        "listing_date",
        "datetime",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "value",
    ]

    df_clean = df_valid[columns_to_keep].copy()

    # Sort by company and datetime
    df_clean = df_clean.sort_values(["code", "datetime"])

    # Save cleaned data
    output_file = "data/raw/intraday/ipo_intraday_2022_2024_clean.csv"
    df_clean.to_csv(output_file, index=False, encoding="utf-8-sig")

    print("=" * 80)
    print("CLEANING COMPLETE")
    print("=" * 80)
    print(f"Output file: {output_file}")
    print(f"Records: {len(df_clean):,}")
    print()

    # Statistics
    print("=" * 80)
    print("DATA STATISTICS")
    print("=" * 80)

    ipo_count = df_clean["code"].nunique()
    avg_candles = len(df_clean) / ipo_count if ipo_count > 0 else 0

    print(f"Unique IPOs: {ipo_count}")
    print(f"Average candles per IPO: {avg_candles:.1f}")
    print()

    # Show sample
    print("Sample data (first 10 records with actual prices):")
    print(
        df_clean[df_clean["close"] > 0]
        .head(10)[["company_name", "datetime", "open", "high", "low", "close", "volume"]]
        .to_string()
    )
    print()

    # Show date range for each IPO
    print("=" * 80)
    print("DATE RANGE BY IPO (First 10)")
    print("=" * 80)

    for code in df_clean["code"].unique()[:10]:
        ipo_data = df_clean[df_clean["code"] == code]
        company_name = ipo_data["company_name"].iloc[0]
        date_min = ipo_data["datetime"].min()
        date_max = ipo_data["datetime"].max()
        record_count = len(ipo_data)

        print(f"{company_name:30} ({code}): {record_count:3} records")
        print(f"  Date range: {date_min} to {date_max}")

    print()


if __name__ == "__main__":
    clean_intraday_data()
