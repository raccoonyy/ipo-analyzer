"""
Merge all IPO datasets: 2018-2021 historical + 2022-2025 current
Handles overlapping 2019 data by deduplicating on stock code
"""

import pandas as pd


def main():
    print("=" * 80)
    print("MERGING ALL IPO DATASETS (2018-2025)")
    print("=" * 80)
    print()

    # 1. Load 2018-2019 data
    print("Loading 2018-2019 historical data...")
    df_38_2018 = pd.read_csv("data/raw/38_historical_2018_2021.csv")
    df_yf_2018 = pd.read_csv("data/raw/yfinance_historical_2018_2021.csv")
    df_2018 = pd.merge(df_38_2018, df_yf_2018, on="code", how="left")

    # Convert date format
    df_2018["listing_date"] = pd.to_datetime(
        df_2018["listing_date"], format="%Y.%m.%d"
    ).dt.strftime("%Y-%m-%d")

    # Filter SPACs
    df_2018 = df_2018[
        ~df_2018["company_name"].str.contains(
            "스팩|SPAC|기업인수목적", na=False, case=False
        )
    ]

    print(f"  2018-2019: {len(df_2018)} IPOs")

    # 2. Load 2019-2021 data (new collection)
    print("Loading 2019-2021 data...")
    df_38_2020 = pd.read_csv("data/raw/38_2020_2021.csv")
    df_yf_2020 = pd.read_csv("data/raw/yfinance_2020_2021.csv")
    df_2020 = pd.merge(df_38_2020, df_yf_2020, on="code", how="left")

    # Convert date format
    df_2020["listing_date"] = pd.to_datetime(
        df_2020["listing_date"], format="%Y.%m.%d"
    ).dt.strftime("%Y-%m-%d")

    print(f"  2019-2021: {len(df_2020)} IPOs")

    # 3. Load 2022-2025 data
    print("Loading 2022-2025 data...")
    df_2022 = pd.read_csv("data/raw/ipo_full_dataset_2022_2025.csv")
    print(f"  2022-2025: {len(df_2022)} IPOs")

    # 4. Combine all datasets
    print("\nCombining datasets...")
    df_combined = pd.concat([df_2018, df_2020, df_2022], ignore_index=True)
    print(f"  Before deduplication: {len(df_combined)} IPOs")

    # 5. Remove duplicates (keep first occurrence by date)
    df_combined = df_combined.sort_values("listing_date")
    df_combined = df_combined.drop_duplicates(subset=["code"], keep="first")
    print(f"  After deduplication: {len(df_combined)} IPOs")

    # 6. Sort by listing date
    df_combined = df_combined.sort_values("listing_date").reset_index(drop=True)

    # 7. Show year distribution
    print("\nYear distribution:")
    for year in [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]:
        count = df_combined[
            df_combined["listing_date"].str.startswith(str(year))
        ].shape[0]
        print(f"  {year}: {count:3} IPOs")

    # 8. Save merged dataset
    output_file = "data/raw/ipo_full_dataset_2018_2025.csv"
    df_combined.to_csv(output_file, index=False)

    print()
    print(f"✅ Saved to: {output_file}")
    print(f"   Total records: {len(df_combined)}")

    # 9. Show sample records
    print("\nSample records:")
    print("-" * 80)
    print(
        df_combined[["code", "company_name", "listing_date", "ipo_price"]]
        .head(10)
        .to_string()
    )
    print()
    print(
        df_combined[["code", "company_name", "listing_date", "ipo_price"]]
        .tail(10)
        .to_string()
    )


if __name__ == "__main__":
    main()
