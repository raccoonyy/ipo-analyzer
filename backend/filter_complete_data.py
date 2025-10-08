"""
Filter Complete IPO Data
Keep only IPOs with complete day0 and day1 price data
"""

import pandas as pd
from pathlib import Path

def filter_complete_data(input_file: str, output_file: str):
    """
    Filter dataset to keep only complete records

    Complete = day0_high > 0 AND day0_close > 0 AND day1_close > 0
    """
    print("=" * 80)
    print("FILTERING COMPLETE IPO DATA")
    print("=" * 80)
    print()

    # Load full dataset
    df = pd.read_csv(input_file)
    print(f"Total records: {len(df)}")

    # Filter complete data
    complete_mask = (
        (df["day0_high"] > 0) &
        (df["day0_close"] > 0) &
        (df["day1_close"] > 0)
    )

    df_complete = df[complete_mask].copy()
    incomplete_count = len(df) - len(df_complete)

    print(f"Complete records: {len(df_complete)} ({len(df_complete)/len(df)*100:.1f}%)")
    print(f"Filtered out: {incomplete_count} records")
    print()

    # Save complete dataset
    df_complete.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"✅ Saved complete dataset to: {output_file}")
    print()

    # Show statistics by year
    print("=" * 80)
    print("BREAKDOWN BY YEAR")
    print("=" * 80)

    df_complete["year"] = pd.to_datetime(df_complete["listing_date"]).dt.year

    for year in sorted(df_complete["year"].unique()):
        year_df = df_complete[df_complete["year"] == year]
        print(f"{year}: {len(year_df)} IPOs")

    print()
    print(f"Total for training: {len(df_complete)} IPOs")
    print()

    # Show sample data
    print("=" * 80)
    print("SAMPLE DATA (First 5 records)")
    print("=" * 80)
    print()
    print(df_complete[["company_name", "code", "listing_date", "day0_high", "day0_close", "day1_close"]].head().to_string())
    print()


if __name__ == "__main__":
    input_file = "data/raw/ipo_full_dataset_2022_2024.csv"
    output_file = "data/raw/ipo_full_dataset_2022_2024_complete.csv"

    filter_complete_data(input_file, output_file)
