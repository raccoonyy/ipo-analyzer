"""
Fix all IPO data discrepancies by updating with 38.co.kr data
"""

import pandas as pd
from pathlib import Path


def fix_dataset(dataset_path: str, subscription_data: pd.DataFrame) -> int:
    """Fix a single dataset file and return number of updates"""
    if not Path(dataset_path).exists():
        print(f"⏭️  Skipping {dataset_path} (not found)")
        return 0

    print(f"\n📄 Processing {Path(dataset_path).name}")

    # Load dataset
    full_dataset = pd.read_csv(dataset_path)
    print(f"   Records: {len(full_dataset)}")

    # Convert code columns to string for comparison
    full_dataset["code"] = full_dataset["code"].astype(str).str.zfill(6)

    # Track changes
    price_updates = 0

    # Process each row in full dataset
    for idx, row in full_dataset.iterrows():
        code = row["code"]

        # Find matching record in subscription data
        sub_match = subscription_data[subscription_data["code"] == code]

        if len(sub_match) == 0:
            continue

        sub_row = sub_match.iloc[0]

        # Update ipo_price_confirmed if different
        if pd.notna(sub_row.get("ipo_price")):
            if (
                pd.isna(row["ipo_price_confirmed"])
                or row["ipo_price_confirmed"] != sub_row["ipo_price"]
            ):
                old_val = row["ipo_price_confirmed"]
                full_dataset.at[idx, "ipo_price_confirmed"] = sub_row["ipo_price"]
                if old_val != sub_row["ipo_price"]:
                    price_updates += 1

        # Update other fields if they exist
        for field in [
            "institutional_demand_rate",
            "subscription_competition_rate",
            "lockup_ratio",
        ]:
            if field in full_dataset.columns and pd.notna(sub_row.get(field)):
                if (
                    pd.isna(row.get(field))
                    or abs(row.get(field, 0) - sub_row[field]) > 0.01
                ):
                    full_dataset.at[idx, field] = sub_row[field]

        # Add shares_offered if available
        if pd.notna(sub_row.get("shares_offered")):
            if "shares_offered" not in full_dataset.columns:
                full_dataset["shares_offered"] = pd.NA
            if pd.isna(row.get("shares_offered")):
                full_dataset.at[idx, "shares_offered"] = sub_row["shares_offered"]

    # Save updated dataset
    full_dataset.to_csv(dataset_path, index=False, encoding="utf-8-sig")

    print(f"   ✅ Updated {price_updates} IPO prices")
    return price_updates


def main():
    print("=" * 80)
    print("FIXING ALL IPO DATA DISCREPANCIES")
    print("=" * 80)
    print()

    # Load subscription data once
    subscription_data = pd.read_csv("data/raw/38_subscription_data.csv")
    subscription_data["code"] = subscription_data["code"].astype(str).str.zfill(6)
    print(f"38 subscription data: {len(subscription_data)} records")

    # Files to update
    files_to_fix = [
        "data/raw/ipo_full_dataset_2022_2025.csv",
        "data/raw/ipo_full_dataset_2022_2024_enhanced.csv",
        "data/raw/ipo_2025_dataset.csv",
        "data/raw/ipo_2025_dataset_enhanced.csv",
        "data/raw/ipo_2025_dataset_yfinance.csv",
    ]

    total_updates = 0
    for file_path in files_to_fix:
        updates = fix_dataset(file_path, subscription_data)
        total_updates += updates

    print()
    print("=" * 80)
    print("FIX COMPLETE")
    print("=" * 80)
    print(f"Total price corrections: {total_updates}")
    print()

    print("⚠️  Next steps:")
    print(
        "  1. Run 'uv run python train_model.py' to retrain model with corrected data"
    )
    print(
        "  2. Run 'uv run python generate_frontend_predictions.py' to regenerate predictions"
    )
    print()


if __name__ == "__main__":
    main()
