"""Update listing_method in existing datasets with correct market classification"""
import pandas as pd

# Load market classification data
df_market = pd.read_csv('data/raw/38_market_classification.csv')

# Normalize listing_method
df_market['listing_method'] = df_market['listing_method'].replace({'코스피': 'KOSPI'})

print("="*80)
print("UPDATING MARKET CLASSIFICATION")
print("="*80)
print(f"\nMarket classification loaded: {len(df_market)} IPOs")
print("\nMarket distribution:")
print(df_market['listing_method'].value_counts())
print()

# Load datasets to update
datasets = [
    'data/raw/ipo_full_dataset_2022_2025.csv',
    'data/raw/ipo_full_dataset_2022_2024_enhanced.csv',
]

for dataset_path in datasets:
    try:
        df = pd.read_csv(dataset_path)
        print(f"\n{'='*80}")
        print(f"Updating: {dataset_path}")
        print(f"{'='*80}")
        print(f"Original size: {len(df)} IPOs")

        # Show original distribution
        if 'listing_method' in df.columns:
            print(f"\nOriginal listing_method distribution:")
            print(df['listing_method'].value_counts())

        # Ensure code is same type in both dataframes
        # Skip rows with invalid codes (non-numeric)
        valid_code_mask = df['code'].astype(str).str.match(r'^\d+$')
        df_valid = df[valid_code_mask].copy()
        df_invalid = df[~valid_code_mask].copy()

        df_valid['code'] = df_valid['code'].astype(int)
        df_market_temp = df_market.copy()
        df_market_temp['code'] = df_market_temp['code'].astype(int)

        # Merge with market classification on code (only valid codes)
        df_valid_updated = df_valid.merge(
            df_market_temp[['code', 'listing_method']],
            on='code',
            how='left',
            suffixes=('_old', '')
        )

        # Drop old listing_method column if it exists
        if 'listing_method_old' in df_valid_updated.columns:
            df_valid_updated = df_valid_updated.drop(columns=['listing_method_old'])

        # Fill missing listing_method with KOSDAQ (default)
        df_valid_updated['listing_method'] = df_valid_updated['listing_method'].fillna('KOSDAQ')

        # Combine valid and invalid rows
        if len(df_invalid) > 0:
            print(f"\nSkipped {len(df_invalid)} rows with invalid codes")
            # Keep original listing_method for invalid rows
            df_updated = pd.concat([df_valid_updated, df_invalid], ignore_index=True)
        else:
            df_updated = df_valid_updated

        print(f"\nUpdated size: {len(df_updated)} IPOs")
        print(f"\nNew listing_method distribution:")
        print(df_updated['listing_method'].value_counts())

        # Save updated dataset
        df_updated.to_csv(dataset_path, index=False, encoding='utf-8-sig')
        print(f"\n✅ Saved updated dataset to: {dataset_path}")

    except Exception as e:
        print(f"Error processing {dataset_path}: {e}")

print("\n" + "="*80)
print("UPDATE COMPLETE")
print("="*80)
