"""Final analysis of 2025 IPO data"""
import pandas as pd

offering = pd.read_csv("data/raw/ipo_offering_info.csv")

# Check all 2025 entries (filter out NA values first)
offering_2025 = offering[offering['listing_date'].notna() & offering['listing_date'].str.startswith('2025')]

print("="*80)
print("2025 IPO DATA ANALYSIS")
print("="*80)
print(f"\nTotal 2025 entries in CSV: {len(offering_2025)}")
print(f"Unique stock codes: {offering_2025['code'].nunique()}")
print(f"Duplicates: {len(offering_2025) - offering_2025['code'].nunique()}")

# Check for duplicates
duplicates = offering_2025[offering_2025.duplicated(subset=['code'], keep=False)]
if len(duplicates) > 0:
    print(f"\nDuplicate entries found:")
    print(duplicates[['code', 'listing_date', 'subscription_period', 'ipo_price']].sort_values('code'))

# Convert listing_date to datetime and extract year properly
offering['listing_dt'] = pd.to_datetime(offering['listing_date'], format='%Y/%m/%d', errors='coerce')
offering['year'] = offering['listing_dt'].dt.year

print(f"\n\n{'='*80}")
print("YEAR DISTRIBUTION (using datetime parsing)")
print("="*80)
print(offering['year'].value_counts().sort_index())

offering_2025_dt = offering[offering['year'] == 2025]
print(f"\n2025 IPOs (datetime parsing): {len(offering_2025_dt)}")
print(f"Unique codes: {offering_2025_dt['code'].nunique()}")

# Check for SPAC codes (contains letters)
spac_codes = offering_2025_dt[offering_2025_dt['code'].astype(str).str.contains('[A-Z]', regex=True)]
print(f"\nSPAC-like codes (contains letters): {len(spac_codes)}")
if len(spac_codes) > 0:
    print("Examples:")
    print(spac_codes[['code', 'listing_date', 'ipo_price']].head(10))

print(f"\n\n{'='*80}")
print("SUMMARY")
print("="*80)
print(f"Total 2025 entries: {len(offering_2025_dt)}")
print(f"Unique stock codes: {offering_2025_dt['code'].nunique()}")
print(f"Regular stock codes: {len(offering_2025_dt[~offering_2025_dt['code'].astype(str).str.contains('[A-Z]', regex=True)])}")
print(f"SPAC-like codes: {len(spac_codes)}")
