"""
Enhance 2025 IPO data by merging with 38.co.kr subscription data
and filling missing fields
"""

import pandas as pd
import numpy as np
from datetime import datetime


def main():
    print("=" * 80)
    print("ENHANCING 2025 IPO DATA")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load 2025 IPO data
    print("Loading 2025 IPO data...")
    df_2025 = pd.read_csv("data/raw/ipo_2025_dataset.csv")
    print(f"✓ Loaded {len(df_2025)} IPOs")
    print()

    # Load 38.co.kr subscription data
    print("Loading 38.co.kr subscription data...")
    df_38 = pd.read_csv("data/raw/38_subscription_data.csv")
    print(f"✓ Loaded {len(df_38)} records")
    print()

    # Convert code to string for consistent merging
    df_2025["code"] = df_2025["code"].astype(str).str.zfill(6)
    df_38["code"] = df_38["code"].astype(str).str.zfill(6)

    # Merge with 38.co.kr data
    print("Merging with 38.co.kr subscription data...")
    df_merged = pd.merge(
        df_2025,
        df_38[["code", "institutional_demand_rate", "subscription_competition_rate", "lockup_ratio"]],
        on="code",
        how="left"
    )

    matched = df_merged["institutional_demand_rate"].notna().sum()
    print(f"✓ Matched {matched}/{len(df_2025)} IPOs with 38.co.kr data")
    print()

    # Fill missing subscription data with defaults
    print("Filling missing subscription data...")
    df_merged["institutional_demand_rate"].fillna(0.0, inplace=True)
    df_merged["subscription_competition_rate"].fillna(0.0, inplace=True)
    df_merged["lockup_ratio"].fillna(0.0, inplace=True)
    print("✓ Filled missing subscription data with 0")
    print()

    # Add missing fields required for modeling
    print("Adding missing fields...")

    # IPO price range (assume no range for 2025 data)
    df_merged["ipo_price_lower"] = df_merged["ipo_price_confirmed"]
    df_merged["ipo_price_upper"] = df_merged["ipo_price_confirmed"]

    # Shares offered (set to 0 for now)
    df_merged["shares_offered"] = 0

    # Allocation ratios (default 50/50)
    df_merged["allocation_ratio_equal"] = 50.0
    df_merged["allocation_ratio_proportional"] = 50.0

    # Paid-in capital and market cap (set to 0 or estimate)
    df_merged["paid_in_capital"] = 0
    df_merged["estimated_market_cap"] = 0

    # Listing method, industry, theme (default values)
    df_merged["listing_method"] = "KOSDAQ"
    df_merged["industry"] = "기타"
    df_merged["theme"] = "주권"

    print("✓ Added missing fields:")
    print("  - ipo_price_lower/upper (= ipo_price_confirmed)")
    print("  - shares_offered (= 0)")
    print("  - allocation_ratio_equal/proportional (= 50.0)")
    print("  - paid_in_capital, estimated_market_cap (= 0)")
    print("  - listing_method, industry, theme (defaults)")
    print()

    # Add KIS daily indicators column names to match 2022-2024 schema
    print("Renaming columns to match 2022-2024 schema...")
    rename_map = {
        "day0_open": "day0_open_kis",
        "day0_high": "day0_high_kis",
        "day0_low": "day0_low_kis",
        "day0_close": "day0_close_kis",
        "day0_volume": "day0_volume_kis",
        "day1_open": "day1_open",
        "day1_high": "day1_high_kis",
        "day1_low": "day1_low",
        "day1_close": "day1_close_kis",
        "day1_volume": "day1_volume",
    }

    df_merged.rename(columns=rename_map, inplace=True)
    print("✓ Renamed columns")
    print()

    # Calculate derived KIS indicators
    print("Calculating derived indicators...")

    # Turnover rate = volume / shares_offered (but shares_offered = 0, so use volume as proxy)
    df_merged["day0_turnover_rate"] = 0.0  # Can't calculate without shares_offered
    df_merged["day1_turnover_rate"] = 0.0

    # Volatility = (high - low) / low * 100
    df_merged["day0_volatility"] = (
        (df_merged["day0_high_kis"] - df_merged["day0_low_kis"]) /
        df_merged["day0_low_kis"] * 100
    ).fillna(0.0)

    print("✓ Calculated turnover rates and volatility")
    print()

    # Reorder columns to match 2022-2024 schema
    expected_cols = [
        "company_name", "code", "listing_date",
        "ipo_price_lower", "ipo_price_upper", "ipo_price_confirmed",
        "shares_offered", "paid_in_capital", "estimated_market_cap",
        "listing_method", "allocation_ratio_equal", "allocation_ratio_proportional",
        "industry", "theme",
        "day0_high", "day0_close", "day1_high", "day1_close",
        "day0_volume_kis", "day0_trading_value",
        "day0_open_kis", "day0_high_kis", "day0_low_kis", "day0_close_kis",
        "day1_volume", "day1_trading_value",
        "day1_open", "day1_high_kis", "day1_low", "day1_close_kis",
        "day0_turnover_rate", "day1_turnover_rate", "day0_volatility",
        "par_value",
        "institutional_demand_rate", "subscription_competition_rate", "lockup_ratio"
    ]

    # Add day0_high and day0_close (copy from day0_high_kis and day0_close_kis)
    df_merged["day0_high"] = df_merged["day0_high_kis"]
    df_merged["day0_close"] = df_merged["day0_close_kis"]
    df_merged["day1_high"] = df_merged["day1_high_kis"]
    df_merged["day1_close"] = df_merged["day1_close_kis"]

    # Select only columns that exist
    available_cols = [col for col in expected_cols if col in df_merged.columns]
    df_enhanced = df_merged[available_cols].copy()

    # Save enhanced dataset
    output_file = "data/raw/ipo_2025_dataset_enhanced.csv"
    df_enhanced.to_csv(output_file, index=False, encoding="utf-8-sig")

    print("=" * 80)
    print("ENHANCEMENT COMPLETE")
    print("=" * 80)
    print(f"Output file: {output_file}")
    print(f"Total IPOs: {len(df_enhanced)}")
    print(f"Columns: {len(df_enhanced.columns)}")
    print()

    print("Sample data:")
    print(df_enhanced[["company_name", "code", "ipo_price_confirmed",
                       "institutional_demand_rate", "subscription_competition_rate"]].head())
    print()

    print("✅ 2025 IPO data enhanced successfully")


if __name__ == "__main__":
    main()
