"""
Fix 명인제약 IPO data with correct values from 38.co.kr
"""

import pandas as pd
from pathlib import Path

# Correct values from 38.co.kr no=2220
CORRECT_DATA = {
    "code": "317450",
    "ipo_price_lower": 45000.0,
    "ipo_price_upper": 58000.0,
    "ipo_price_confirmed": 58000.0,
    "institutional_demand_rate": 488.95,
    "subscription_competition_rate": 587.00,
    "lockup_ratio": 73.81,
}

def fix_csv_file(file_path: Path):
    """Fix 명인제약 data in a CSV file"""
    if not file_path.exists():
        print(f"⏭️  Skipping {file_path} (not found)")
        return False

    print(f"\n📄 Processing {file_path.name}")

    # Read CSV
    df = pd.read_csv(file_path)

    # Check if 명인제약 exists
    mask = df["code"].astype(str) == CORRECT_DATA["code"]
    if not mask.any():
        print(f"   ⏭️  명인제약 not found")
        return False

    # Show current values
    row = df[mask].iloc[0]
    print(f"   Current values:")
    print(f"     price_lower: {row.get('ipo_price_lower', 'N/A')}")
    print(f"     institutional: {row.get('institutional_demand_rate', 'N/A')}")
    print(f"     subscription: {row.get('subscription_competition_rate', 'N/A')}")
    print(f"     lockup: {row.get('lockup_ratio', 'N/A')}")

    # Update values
    for col, value in CORRECT_DATA.items():
        if col in df.columns:
            df.loc[mask, col] = value

    # Save back
    df.to_csv(file_path, index=False, encoding="utf-8-sig")

    print(f"   ✅ Updated to correct values:")
    print(f"     price_lower: {CORRECT_DATA['ipo_price_lower']}")
    print(f"     institutional: {CORRECT_DATA['institutional_demand_rate']}")
    print(f"     subscription: {CORRECT_DATA['subscription_competition_rate']}")
    print(f"     lockup: {CORRECT_DATA['lockup_ratio']}")

    return True


def main():
    """Fix 명인제약 data in all relevant CSV files"""
    print("=" * 80)
    print("FIXING 명인제약 IPO DATA")
    print("=" * 80)
    print(f"Updating with correct values from 38.co.kr")
    print()

    # List of files to update
    files_to_fix = [
        "data/raw/ipo_full_dataset_2022_2025.csv",
        "data/raw/ipo_2025_dataset.csv",
        "data/raw/ipo_2025_dataset_enhanced.csv",
        "data/raw/ipo_2025_dataset_yfinance.csv",
    ]

    updated_count = 0
    for file_path in files_to_fix:
        path = Path(file_path)
        if fix_csv_file(path):
            updated_count += 1

    print()
    print("=" * 80)
    print("FIX COMPLETE")
    print("=" * 80)
    print(f"Updated {updated_count}/{len(files_to_fix)} files")
    print()

    if updated_count > 0:
        print("⚠️  Next steps:")
        print("  1. Run 'python generate_frontend_predictions.py' to regenerate predictions")
        print("  2. Copy the JSON file to frontend/public/")
    print()


if __name__ == "__main__":
    main()
