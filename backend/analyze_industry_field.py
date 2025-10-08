"""Analyze industry and theme fields in datasets"""
import pandas as pd

print("="*80)
print("INDUSTRY & THEME FIELD ANALYSIS")
print("="*80)

# Check enhanced dataset
enhanced = pd.read_csv("data/raw/ipo_full_dataset_2022_2024_enhanced.csv")

print("\n1. INDUSTRY FIELD")
print("-"*80)
print(f"Total IPOs: {len(enhanced)}")
print(f"\nUnique industry values:")
print(enhanced['industry'].value_counts())

print("\n2. THEME FIELD")
print("-"*80)
print(f"Unique theme values:")
print(enhanced['theme'].value_counts())

# Sample records
print("\n3. SAMPLE RECORDS")
print("-"*80)
print(enhanced[['code', 'company_name', 'industry', 'theme', 'listing_date']].head(20).to_string())

# Check main dataset
print("\n\n" + "="*80)
print("MAIN DATASET CHECK")
print("="*80)

main = pd.read_csv("data/raw/ipo_full_dataset_2022_2024.csv")
print(f"\nTotal IPOs: {len(main)}")
print(f"\nUnique industry values in main dataset:")
print(main['industry'].value_counts())
print(f"\nUnique theme values in main dataset:")
print(main['theme'].value_counts())

# Check a specific IPO from KRX API directly
print("\n\n" + "="*80)
print("KRX API DATA STRUCTURE")
print("="*80)
print("\nChecking what fields KRX API provides...")
print("Need to call KRX API to see the actual industry field")
