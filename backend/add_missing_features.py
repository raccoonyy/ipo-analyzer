"""
Add missing features to the dataset for model prediction
"""

import pandas as pd

def add_missing_features():
    """Add listing_per, listing_pbr, listing_eps features"""
    print("=" * 80)
    print("ADDING MISSING FEATURES")
    print("=" * 80)
    print()

    # Load dataset
    file_path = "data/raw/ipo_full_dataset_2022_2025.csv"
    df = pd.read_csv(file_path)

    print(f"Loaded {len(df)} records from {file_path}")
    print()

    # Add missing columns if they don't exist
    if 'listing_per' not in df.columns:
        # Use day0_per if available, otherwise 0
        if 'day0_per' in df.columns:
            df['listing_per'] = df['day0_per'].fillna(0)
            print("✅ Added listing_per (copied from day0_per)")
        else:
            df['listing_per'] = 0
            print("✅ Added listing_per (filled with 0)")

    if 'listing_pbr' not in df.columns:
        if 'day0_pbr' in df.columns:
            df['listing_pbr'] = df['day0_pbr'].fillna(0)
            print("✅ Added listing_pbr (copied from day0_pbr)")
        else:
            df['listing_pbr'] = 0
            print("✅ Added listing_pbr (filled with 0)")

    if 'listing_eps' not in df.columns:
        if 'day0_eps' in df.columns:
            df['listing_eps'] = df['day0_eps'].fillna(0)
            print("✅ Added listing_eps (copied from day0_eps)")
        else:
            df['listing_eps'] = 0
            print("✅ Added listing_eps (filled with 0)")

    # Save back
    df.to_csv(file_path, index=False, encoding="utf-8-sig")

    print()
    print("=" * 80)
    print("FEATURES ADDED")
    print("=" * 80)
    print(f"Updated: {file_path}")
    print()


if __name__ == "__main__":
    add_missing_features()
