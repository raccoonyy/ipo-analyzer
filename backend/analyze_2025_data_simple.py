"""
Analyze 2025 IPO data discrepancy
"""

import pandas as pd
import requests
from src.config.settings import settings

print("=" * 80)
print("ANALYZING 2025 IPO DATA")
print("=" * 80)
print()

# 1. Get 2025 IPOs from KRX API (direct call)
print("1. Fetching 2025 IPOs from KRX API...")

url = "https://data-dbg.krx.co.kr/svc/apis/sto/ksq_isu_base_info"
headers = {
    "AUTH_KEY": settings.KRX_API_KEY,
    "Content-Type": "application/json",
}
params = {"basDd": "20251231"}

response = requests.get(url, params=params, headers=headers, timeout=30)
data = response.json()

if response.status_code == 200 and "OutBlock_1" in data:
    all_stocks = data["OutBlock_1"]

    # Filter to 2025 IPOs
    krx_2025 = [
        stock for stock in all_stocks
        if stock.get("LIST_DD", "").startswith("2025")
    ]

    print(f"   Total stocks from KRX: {len(all_stocks)}")
    print(f"   2025 IPOs from KRX: {len(krx_2025)}")

    krx_df = pd.DataFrame(krx_2025)
    krx_df['code'] = krx_df['ISU_SRT_CD'].astype(str).str.zfill(6)
    krx_df['listing_date'] = krx_df['LIST_DD']
    krx_df['company_name'] = krx_df['ISU_NM']

    print("\n   Sample KRX 2025 IPOs:")
    print(krx_df[['code', 'company_name', 'listing_date']].head(10).to_string())
else:
    print(f"   ❌ Failed to fetch from KRX: {response.status_code}")
    krx_df = pd.DataFrame()

print()

# 2. Get 2025 IPOs from KIS offering data
print("2. Loading 2025 IPOs from KIS offering data...")
kis_offering = pd.read_csv("data/raw/ipo_offering_info.csv")
kis_offering['code'] = kis_offering['code'].astype(str).str.zfill(6)

# Filter 2025 IPOs (listing_date format: 2025/09/30)
kis_2025 = kis_offering[kis_offering['listing_date'].str.startswith('2025')]
print(f"   2025 IPOs from KIS: {len(kis_2025)}")

print("\n   Sample KIS 2025 IPOs:")
print(kis_2025[['code', 'ipo_price', 'listing_date']].head(10).to_string())
print()

# 3. Compare
print("=" * 80)
print("COMPARISON")
print("=" * 80)

if not krx_df.empty:
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
        for code in sorted(missing_in_kis):
            stock = krx_df[krx_df['code'] == code].iloc[0]
            print(f"  {code} - {stock['company_name']:30} (상장일: {stock['listing_date']})")
        print()

    # Extra in KIS (codes not in KRX)
    extra_in_kis = kis_codes - krx_codes
    if extra_in_kis:
        print(f"Extra in KIS offering data ({len(extra_in_kis)} IPOs):")
        for code in sorted(extra_in_kis):
            print(f"  {code}")
        print()

# Check our main dataset
print("=" * 80)
print("MAIN DATASET CHECK")
print("=" * 80)

try:
    main_df = pd.read_csv("data/raw/ipo_full_dataset_2022_2024.csv")
    main_df['code'] = main_df['code'].astype(str).str.zfill(6)
    main_df['listing_date'] = pd.to_datetime(main_df['listing_date'])

    # 2025 in main dataset
    main_2025 = main_df[main_df['listing_date'].dt.year == 2025]
    print(f"2025 IPOs in main dataset: {len(main_2025)}")

    if len(main_2025) > 0:
        print("\nSample:")
        print(main_2025[['code', 'company_name', 'listing_date']].head().to_string())
except Exception as e:
    print(f"Error reading main dataset: {e}")
    main_2025 = pd.DataFrame()

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
if not krx_df.empty:
    print(f"KRX API (2025): {len(krx_codes)} IPOs")
    print(f"KIS Offering API (2025): {len(kis_codes)} IPOs")
    print(f"Main dataset (2025): {len(main_2025)} IPOs")
    print(f"Missing from KIS: {len(missing_in_kis)}")
else:
    print("Unable to compare - KRX data not available")
