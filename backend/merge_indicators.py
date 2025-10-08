"""
Merge Daily Indicators with Main Dataset
Combine KIS API data with existing IPO dataset
"""

import pandas as pd
from pathlib import Path

def merge_daily_indicators():
    """Merge daily indicators with main dataset"""
    print("=" * 80)
    print("MERGING DAILY INDICATORS")
    print("=" * 80)
    print()

    # Load main dataset
    main_file = "data/raw/ipo_full_dataset_2022_2024_complete.csv"
    df_main = pd.read_csv(main_file)
    print(f"Loaded main dataset: {len(df_main)} IPOs")

    # Filter out SPAC companies
    initial_count = len(df_main)
    df_main = df_main[
        (~df_main["company_name"].str.contains("기업인수목적", na=False)) &
        (~df_main["industry"].str.contains("SPAC", na=False))
    ]
    spac_count = initial_count - len(df_main)
    print(f"Filtered out {spac_count} SPAC companies")
    print(f"Remaining IPOs: {len(df_main)}")
    print()

    # Load daily indicators
    indicators_file = "data/raw/daily_indicators/ipo_daily_indicators_2022_2024.csv"
    df_indicators = pd.read_csv(indicators_file)
    print(f"Loaded daily indicators: {len(df_indicators)} records")
    print()

    # Parse dates
    df_indicators["date"] = pd.to_datetime(df_indicators["date"])
    df_main["listing_date"] = pd.to_datetime(df_main["listing_date"])

    # Separate day 0 and day 1 data
    print("Separating day 0 and day 1 data...")

    # Group by code and get first 2 records
    df_indicators_sorted = df_indicators.sort_values(["code", "date"])

    # Day 0 (first record per IPO)
    df_day0 = df_indicators_sorted.groupby("code").first().reset_index()
    df_day0 = df_day0.rename(columns={
        "volume": "day0_volume_kis",
        "trading_value": "day0_trading_value",
        "open": "day0_open_kis",
        "high": "day0_high_kis",
        "low": "day0_low_kis",
        "close": "day0_close_kis",
        # Financial metrics
        "per": "day0_per",
        "pbr": "day0_pbr",
        "eps": "day0_eps",
        "market_cap": "day0_market_cap",
        "listed_shares": "day0_listed_shares",
    })

    # Day 1 (second record per IPO)
    df_day1 = df_indicators_sorted.groupby("code").nth(1).reset_index()
    df_day1 = df_day1.rename(columns={
        "volume": "day1_volume",
        "trading_value": "day1_trading_value",
        "open": "day1_open",
        "high": "day1_high_kis",
        "low": "day1_low",
        "close": "day1_close_kis",
        # Financial metrics
        "per": "day1_per",
        "pbr": "day1_pbr",
        "eps": "day1_eps",
        "market_cap": "day1_market_cap",
    })

    print(f"Day 0 records: {len(df_day0)}")
    print(f"Day 1 records: {len(df_day1)}")
    print()

    # Select columns to merge
    day0_cols = ["code", "day0_volume_kis", "day0_trading_value", "day0_open_kis",
                 "day0_high_kis", "day0_low_kis", "day0_close_kis",
                 "day0_per", "day0_pbr", "day0_eps", "day0_market_cap", "day0_listed_shares"]
    day1_cols = ["code", "day1_volume", "day1_trading_value", "day1_open",
                 "day1_high_kis", "day1_low", "day1_close_kis",
                 "day1_per", "day1_pbr", "day1_eps", "day1_market_cap"]

    df_day0_merge = df_day0[day0_cols]
    df_day1_merge = df_day1[day1_cols]

    # Merge with main dataset
    print("Merging with main dataset...")
    df_merged = df_main.copy()

    # Merge day 0 data
    df_merged = df_merged.merge(df_day0_merge, on="code", how="left")

    # Merge day 1 data
    df_merged = df_merged.merge(df_day1_merge, on="code", how="left")

    print(f"Merged dataset: {len(df_merged)} IPOs")
    print()

    # Calculate additional features
    print("Calculating additional features...")

    # Day 0 turnover rate (거래량 회전율)
    df_merged["day0_turnover_rate"] = (
        df_merged["day0_volume_kis"] / df_merged["shares_offered"]
    ) * 100

    # Day 1 turnover rate
    df_merged["day1_turnover_rate"] = (
        df_merged["day1_volume"] / df_merged["shares_offered"]
    ) * 100

    # Price volatility (day 0)
    df_merged["day0_volatility"] = (
        (df_merged["day0_high_kis"] - df_merged["day0_low_kis"]) /
        df_merged["day0_open_kis"]
    ) * 100

    print("✅ Added calculated features:")
    print("   - day0_turnover_rate")
    print("   - day1_turnover_rate")
    print("   - day0_volatility")
    print()

    # Show statistics
    print("=" * 80)
    print("MERGED DATA STATISTICS")
    print("=" * 80)

    new_cols = [
        "day0_volume_kis", "day0_trading_value", "day1_volume", "day1_trading_value",
        "day0_turnover_rate", "day1_turnover_rate", "day0_volatility",
        "day0_per", "day0_pbr", "day0_eps", "day0_market_cap", "day0_listed_shares",
        "day1_per", "day1_pbr", "day1_eps", "day1_market_cap"
    ]

    for col in new_cols:
        non_null = df_merged[col].notna().sum()
        print(f"{col:30}: {non_null}/{len(df_merged)} ({non_null/len(df_merged)*100:.1f}%) non-null")

    print()

    # Save merged dataset
    output_file = "data/raw/ipo_full_dataset_2022_2024_enhanced.csv"
    df_merged.to_csv(output_file, index=False, encoding="utf-8-sig")

    print("=" * 80)
    print("MERGE COMPLETE")
    print("=" * 80)
    print(f"Output file: {output_file}")
    print(f"Total columns: {len(df_merged.columns)}")
    print()

    # Show sample
    print("Sample data (first 5 records with new columns):")
    sample_cols = ["company_name", "code", "day0_close", "day0_volume_kis",
                   "day0_trading_value", "day0_turnover_rate"]
    print(df_merged[sample_cols].head().to_string())
    print()

    # Show column list
    print("=" * 80)
    print("ALL COLUMNS IN ENHANCED DATASET")
    print("=" * 80)
    for i, col in enumerate(df_merged.columns, 1):
        print(f"{i:2}. {col}")
    print()


if __name__ == "__main__":
    merge_daily_indicators()
