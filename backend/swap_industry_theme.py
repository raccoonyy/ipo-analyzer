"""
Swap industry and theme fields in existing datasets

Original mapping (incorrect):
- industry = SECUGRP_NM (always "주권")
- theme = SECT_TP_NM (actual classification)

New mapping (correct):
- industry = SECT_TP_NM (KOSDAQ sector classification)
- theme = SECUGRP_NM (security group)
"""

import pandas as pd
from pathlib import Path

print("="*80)
print("SWAPPING INDUSTRY AND THEME FIELDS")
print("="*80)
print()

datasets = [
    "data/raw/ipo_full_dataset_2022_2024.csv",
    "data/raw/ipo_full_dataset_2022_2024_enhanced.csv",
]

for dataset_file in datasets:
    path = Path(dataset_file)

    if not path.exists():
        print(f"⚠️  Skipping {dataset_file} (not found)")
        continue

    print(f"Processing: {dataset_file}")
    print("-"*80)

    # Read dataset
    df = pd.read_csv(path)

    # Show before
    print(f"Before swap:")
    print(f"  industry unique values: {df['industry'].unique().tolist()}")
    print(f"  theme unique values: {df['theme'].unique().tolist()[:10]}...")

    # Swap columns
    df['industry'], df['theme'] = df['theme'], df['industry']

    # Show after
    print(f"\nAfter swap:")
    print(f"  industry unique values: {df['industry'].unique().tolist()[:10]}...")
    print(f"  theme unique values: {df['theme'].unique().tolist()}")

    # Save
    df.to_csv(path, index=False)
    print(f"✅ Saved {len(df)} records to {dataset_file}")
    print()

print("="*80)
print("SWAP COMPLETE")
print("="*80)
print("\nVerifying changes...")

# Verify
for dataset_file in datasets:
    path = Path(dataset_file)
    if path.exists():
        df = pd.read_csv(path)
        print(f"\n{dataset_file}:")
        print(f"  Sample industry values: {df['industry'].value_counts().head(5).to_dict()}")
        print(f"  Sample theme values: {df['theme'].value_counts().to_dict()}")
