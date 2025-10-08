"""
Validate all IPO data by comparing with 38.co.kr subscription data
"""

import pandas as pd
import numpy as np
from pathlib import Path


def main():
    print("=" * 80)
    print("VALIDATING ALL IPO DATA")
    print("=" * 80)
    print()

    # Load datasets
    full_dataset = pd.read_csv("data/raw/ipo_full_dataset_2022_2025.csv")
    subscription_data = pd.read_csv("data/raw/38_subscription_data.csv")

    print(f"Full dataset: {len(full_dataset)} records")
    print(f"38 subscription data: {len(subscription_data)} records")
    print()

    # Convert code columns to string for comparison
    full_dataset["code"] = full_dataset["code"].astype(str).str.zfill(6)
    subscription_data["code"] = subscription_data["code"].astype(str).str.zfill(6)

    # Merge on code to compare
    merged = full_dataset.merge(
        subscription_data, on="code", how="left", suffixes=("_full", "_38")
    )

    print("=" * 80)
    print("COMPARING DATA FIELDS")
    print("=" * 80)
    print()

    # Fields to compare
    fields_to_check = [
        ("ipo_price_confirmed", "ipo_price"),
        ("institutional_demand_rate", "institutional_demand_rate"),
        ("subscription_competition_rate", "subscription_competition_rate"),
        ("lockup_ratio", "lockup_ratio"),
        ("shares_offered", "shares_offered"),
    ]

    discrepancies = []

    for full_field, sub_field in fields_to_check:
        full_col = (
            f"{full_field}_full"
            if full_field
            in [
                "institutional_demand_rate",
                "subscription_competition_rate",
                "lockup_ratio",
                "shares_offered",
            ]
            else full_field
        )
        sub_col = (
            f"{sub_field}_38"
            if sub_field
            in [
                "institutional_demand_rate",
                "subscription_competition_rate",
                "lockup_ratio",
                "shares_offered",
            ]
            else sub_field
        )

        # Check if columns exist
        if full_col not in merged.columns or sub_col not in merged.columns:
            print(f"⚠️  Column not found: {full_col} or {sub_col}")
            continue

        print(f"\nChecking: {full_field}")
        print("-" * 80)

        # Compare values where both exist
        mask = merged[full_col].notna() & merged[sub_col].notna()

        if mask.sum() == 0:
            print(f"  No overlapping data")
            continue

        # For price fields, check exact match
        if "price" in full_field:
            diff_mask = mask & (merged[full_col] != merged[sub_col])
        else:
            # For other fields, allow small tolerance (0.1%)
            diff_mask = mask & (np.abs(merged[full_col] - merged[sub_col]) > 0.01)

        if diff_mask.sum() > 0:
            print(f"  ⚠️  Found {diff_mask.sum()} discrepancies:")
            for idx in merged[diff_mask].index:  # Save ALL discrepancies
                row = merged.loc[idx]
                company = row.get(
                    "company_name_full", row.get("company_name_38", "Unknown")
                )
                code = row["code"]
                full_val = row[full_col]
                sub_val = row[sub_col]

                discrepancies.append(
                    {
                        "code": code,
                        "company": company,
                        "field": full_field,
                        "full_dataset_value": full_val,
                        "38_value": sub_val,
                    }
                )

            # Show first 10 in console
            for idx in merged[diff_mask].index[:10]:
                row = merged.loc[idx]
                company = row.get(
                    "company_name_full", row.get("company_name_38", "Unknown")
                )
                code = row["code"]
                full_val = row[full_col]
                sub_val = row[sub_col]
                print(f"     {company} ({code}): {full_val} → {sub_val}")

            if diff_mask.sum() > 10:
                print(f"     ... and {diff_mask.sum() - 10} more")
        else:
            print(f"  ✓ All values match")

    print()
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total discrepancies found: {len(discrepancies)}")
    print()

    if discrepancies:
        # Save discrepancies to CSV for review
        disc_df = pd.DataFrame(discrepancies)
        disc_df.to_csv(
            "data/raw/data_discrepancies.csv", index=False, encoding="utf-8-sig"
        )
        print(f"✅ Saved discrepancies to: data/raw/data_discrepancies.csv")
        print()

        # Show summary by field
        print("Discrepancies by field:")
        print(disc_df.groupby("field").size())
    else:
        print("✅ No discrepancies found!")

    print()


if __name__ == "__main__":
    main()
