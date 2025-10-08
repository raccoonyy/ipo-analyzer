"""
Merge 38.co.kr subscription data into existing datasets
"""

import pandas as pd
import numpy as np


def normalize_company_name(name):
    """Normalize company name for matching"""
    if pd.isna(name):
        return ""
    # Remove whitespace and special characters
    return name.strip().replace(" ", "").replace("(주)", "").replace("㈜", "")


def normalize_listing_date(date_str):
    """Normalize listing date to YYYY-MM-DD format"""
    if pd.isna(date_str):
        return ""

    date_str = str(date_str).strip()

    # Handle format: "2022.01.20" -> "2022-01-20"
    if "." in date_str:
        parts = date_str.split(".")
        if len(parts) == 3:
            year, month, day = parts
            # Handle 2-digit year
            if len(year) == 2:
                year = "20" + year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    # Already in YYYY-MM-DD format
    if "-" in date_str and len(date_str) == 10:
        return date_str

    return date_str


def merge_subscription_data():
    """Merge 38.co.kr subscription data into main datasets"""

    print("=" * 80)
    print("MERGING SUBSCRIPTION DATA")
    print("=" * 80)
    print()

    # Load 38.co.kr subscription data
    print("Loading 38.co.kr subscription data...")
    df_38 = pd.read_csv("data/raw/38_subscription_data.csv")
    print(f"  Loaded {len(df_38)} records from 38.co.kr")
    print()

    # Normalize for matching
    df_38["company_name_norm"] = df_38["company_name"].apply(normalize_company_name)
    df_38["listing_date_norm"] = df_38["listing_date"].apply(normalize_listing_date)
    df_38["code"] = df_38["code"].astype(str).str.zfill(6)

    # Create lookup key: code + listing_date
    df_38["lookup_key"] = df_38["code"] + "_" + df_38["listing_date_norm"]

    # Select columns to merge
    subscription_cols = [
        "lookup_key",
        "institutional_demand_rate",
        "subscription_competition_rate",
        "lockup_ratio",
    ]
    df_38_lookup = df_38[subscription_cols].copy()

    # Datasets to update
    datasets = [
        "data/raw/ipo_full_dataset_2022_2024.csv",
        "data/raw/ipo_full_dataset_2022_2024_enhanced.csv",
    ]

    for dataset_file in datasets:
        print(f"Processing: {dataset_file}")
        print("-" * 80)

        # Load dataset
        df = pd.read_csv(dataset_file)
        print(f"  Original records: {len(df)}")

        # Normalize dataset
        df["code"] = df["code"].astype(str).str.zfill(6)
        df["listing_date_norm"] = df["listing_date"].apply(normalize_listing_date)
        df["lookup_key"] = df["code"] + "_" + df["listing_date_norm"]

        # Count existing non-zero values
        before_nonzero = {
            "institutional_demand_rate": (df["institutional_demand_rate"] != 0).sum(),
            "subscription_competition_rate": (
                df["subscription_competition_rate"] != 0
            ).sum(),
            "lockup_ratio": (df["lockup_ratio"] != 0).sum(),
        }

        print(f"\n  Before merge (non-zero values):")
        for field, count in before_nonzero.items():
            print(f"    {field:35}: {count}")

        # Merge subscription data
        # Drop existing subscription columns
        df = df.drop(
            columns=[
                "institutional_demand_rate",
                "subscription_competition_rate",
                "lockup_ratio",
            ]
        )

        # Merge with 38.co.kr data
        df = df.merge(df_38_lookup, on="lookup_key", how="left")

        # Fill NaN with 0.0 for unmatched records
        df["institutional_demand_rate"] = df["institutional_demand_rate"].fillna(0.0)
        df["subscription_competition_rate"] = df[
            "subscription_competition_rate"
        ].fillna(0.0)
        df["lockup_ratio"] = df["lockup_ratio"].fillna(0.0)

        # Count after merge
        after_nonzero = {
            "institutional_demand_rate": (df["institutional_demand_rate"] != 0).sum(),
            "subscription_competition_rate": (
                df["subscription_competition_rate"] != 0
            ).sum(),
            "lockup_ratio": (df["lockup_ratio"] != 0).sum(),
        }

        print(f"\n  After merge (non-zero values):")
        for field, count in after_nonzero.items():
            improvement = count - before_nonzero[field]
            print(f"    {field:35}: {count} (+{improvement})")

        # Drop temporary columns
        df = df.drop(columns=["listing_date_norm", "lookup_key"])

        # Save updated dataset
        df.to_csv(dataset_file, index=False)
        print(f"\n  ✅ Saved updated dataset to {dataset_file}")
        print()

    print("=" * 80)
    print("MERGE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    merge_subscription_data()
