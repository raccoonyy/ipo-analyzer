"""
Analyze 2025 IPO data discrepancy between KRX and KIS APIs
"""

import pandas as pd
from src.api.krx_client import KRXApiClient
from src.config.settings import settings

print("=" * 80)
print("ANALYZING 2025 IPO DATA DISCREPANCY")
print("=" * 80)
print()

# 1. Get 2025 IPOs from KRX API
print("1. Fetching 2025 IPOs from KRX API...")
krx_client = KRXApiClient(api_key=settings.KRX_API_KEY)

krx_stocks = krx_client.get_stock_info(base_date="20251231")
print(f"   Total stocks from KRX: {len(krx_stocks)}")

# Filter to 2025 IPOs
krx_2025 = [
    stock for stock in krx_stocks
    if stock.get("LIST_DD", "").startswith("2025")
]
print(f"   2025 IPOs from KRX: {len(krx_2025)}")
print()

# Create KRX DataFrame
krx_df = pd.DataFrame(krx_2025)
krx_df['code'] = krx_df['ISU_SRT_CD'].astype(str).str.zfill(6)
krx_df['listing_date'] = krx_df['LIST_DD']
krx_df['company_name'] = krx_df['ISU_NM']

print("   Sample KRX 2025 IPOs:")
print(krx_df[['code', 'company_name', 'listing_date']].head(10))
print()

# 2. Get 2025 IPOs from KIS offering data
print("2. Loading 2025 IPOs from KIS offering data...")
kis_offering = pd.read_csv("data/raw/ipo_offering_info.csv")
kis_offering['code'] = kis_offering['code'].astype(str).str.zfill(6)

# Filter 2025 IPOs
kis_2025 = kis_offering[kis_offering['listing_date'].str.startswith('2025')]
print(f"   2025 IPOs from KIS: {len(kis_2025)}")
print()

print("   Sample KIS 2025 IPOs:")
print(kis_2025[['code', 'ipo_price', 'listing_date']].head(10))
print()

# 3. Compare
print("=" * 80)
print("COMPARISON")
print("=" * 80)

krx_codes = set(krx_df['code'].tolist())
kis_codes = set(kis_2025['code'].tolist())

print(f"KRX 2025 IPOs: {len(krx_codes)}")
print(f"KIS 2025 IPOs: {len(kis_codes)}")
print(f"Difference: {len(krx_codes) - len(kis_codes)}")
print()

# Missing in KIS
missing_in_kis = krx_codes - kis_codes
if missing_in_kis:
    print(f"Missing in KIS offering data ({len(missing_in_kis)} IPOs):")
    for code in missing_in_kis:
        stock = krx_df[krx_df['code'] == code].iloc[0]
        print(f"  {code} - {stock['company_name']} (상장일: {stock['listing_date']})")
    print()

# Extra in KIS
extra_in_kis = kis_codes - krx_codes
if extra_in_kis:
    print(f"Extra in KIS offering data ({len(extra_in_kis)} IPOs):")
    for code in extra_in_kis:
        stock = kis_2025[kis_2025['code'] == code].iloc[0]
        print(f"  {code} - {stock.get('listing_date', 'N/A')}")
    print()

# Check our main dataset
print("=" * 80)
print("MAIN DATASET CHECK")
print("=" * 80)

main_df = pd.read_csv("data/raw/ipo_full_dataset_2022_2024.csv")
main_df['code'] = main_df['code'].astype(str).str.zfill(6)
main_df['listing_date'] = pd.to_datetime(main_df['listing_date'])

# 2025 in main dataset
main_2025 = main_df[main_df['listing_date'].dt.year == 2025]
print(f"2025 IPOs in main dataset: {len(main_2025)}")

if len(main_2025) > 0:
    print("Sample:")
    print(main_2025[['code', 'company_name', 'listing_date']].head())

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"KRX API (2025): {len(krx_codes)} IPOs")
print(f"KIS Offering API (2025): {len(kis_codes)} IPOs")
print(f"Main dataset (2025): {len(main_2025)} IPOs")
print(f"Missing from KIS: {len(missing_in_kis)}")
print(f"Extra in KIS: {len(extra_in_kis)}")
