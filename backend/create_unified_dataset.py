"""
Create unified 2022-2025 IPO dataset by combining historical and 2025 data
"""

import pandas as pd
from datetime import datetime


def main():
    print("=" * 80)
    print("CREATING UNIFIED 2022-2025 DATASET")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load 2022-2024 data
    print("Loading 2022-2024 data...")
    df_historical = pd.read_csv("data/raw/ipo_full_dataset_2022_2024_enhanced.csv")
    print(f"✓ Loaded {len(df_historical)} IPOs from 2022-2024")
    print()

    # Load enhanced 2025 data
    print("Loading enhanced 2025 data...")
    df_2025 = pd.read_csv("data/raw/ipo_2025_dataset_enhanced.csv")
    print(f"✓ Loaded {len(df_2025)} IPOs from 2025")
    print()

    # Check column alignment
    print("Checking column alignment...")
    historical_cols = set(df_historical.columns)
    df_2025_cols = set(df_2025.columns)

    missing_in_2025 = historical_cols - df_2025_cols
    missing_in_historical = df_2025_cols - historical_cols

    if missing_in_2025:
        print(f"Columns in 2022-2024 but missing in 2025: {missing_in_2025}")
        # Add missing columns to 2025 with default values
        for col in missing_in_2025:
            df_2025[col] = 0 if df_historical[col].dtype in ['int64', 'float64'] else ""

    if missing_in_historical:
        print(f"Columns in 2025 but missing in 2022-2024: {missing_in_historical}")
        # Add missing columns to historical with default values
        for col in missing_in_historical:
            df_historical[col] = 0 if df_2025[col].dtype in ['int64', 'float64'] else ""

    print("✓ Columns aligned")
    print()

    # Combine datasets
    print("Combining datasets...")
    df_combined = pd.concat([df_historical, df_2025], ignore_index=True)
    print(f"✓ Combined dataset: {len(df_combined)} IPOs")
    print()

    # Sort by listing date
    df_combined["listing_date"] = pd.to_datetime(
        df_combined["listing_date"], errors="coerce"
    )
    df_combined = df_combined.sort_values("listing_date").reset_index(drop=True)

    # Save unified dataset
    output_file = "data/raw/ipo_full_dataset_2022_2025.csv"
    df_combined.to_csv(output_file, index=False, encoding="utf-8-sig")

    print("=" * 80)
    print("UNIFIED DATASET CREATED")
    print("=" * 80)
    print(f"Output file: {output_file}")
    print(f"Total IPOs: {len(df_combined)}")
    print(f"Columns: {len(df_combined.columns)}")
    print()

    # Show year distribution
    print("Year distribution:")
    df_combined["year"] = df_combined["listing_date"].dt.year
    year_counts = df_combined["year"].value_counts().sort_index()
    for year, count in year_counts.items():
        print(f"  {int(year)}: {count} IPOs")
    print()

    # Show data completeness for key fields
    print("Data completeness for key fields:")
    key_fields = [
        "ipo_price_lower",
        "ipo_price_upper",
        "ipo_price_confirmed",
        "day0_close",
        "day1_close",
        "institutional_demand_rate",
        "subscription_competition_rate",
    ]

    for field in key_fields:
        if field in df_combined.columns:
            completeness = df_combined[field].notna().sum() / len(df_combined) * 100
            print(f"  {field}: {completeness:.1f}%")

    print()
    print("✅ Unified dataset created successfully")


if __name__ == "__main__":
    main()
