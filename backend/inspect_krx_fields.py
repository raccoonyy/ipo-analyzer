"""Inspect actual KRX API response fields"""
import requests
from src.config.settings import settings
import json

print("="*80)
print("KRX API FIELD INSPECTION")
print("="*80)

url = "https://data-dbg.krx.co.kr/svc/apis/sto/ksq_isu_base_info"
headers = {
    "AUTH_KEY": settings.KRX_API_KEY,
    "Content-Type": "application/json",
}

# Get recent data
params = {"basDd": "20241231"}

print(f"\nCalling KRX API: {url}")
print(f"Params: {params}")
print()

response = requests.get(url, params=params, headers=headers, timeout=30)

if response.status_code == 200:
    data = response.json()
    stocks = data.get("OutBlock_1", [])

    print(f"✅ Retrieved {len(stocks)} stocks")
    print()

    # Find a recent IPO
    recent_ipos = [s for s in stocks if s.get("LIST_DD", "").startswith("2024")]

    if recent_ipos:
        print(f"Found {len(recent_ipos)} IPOs from 2024")
        print()

        # Show first 5 IPOs with all fields
        print("Sample IPO Records (all fields):")
        print("-"*80)

        for i, ipo in enumerate(recent_ipos[:5], 1):
            print(f"\n{i}. {ipo.get('ISU_NM', 'N/A')} ({ipo.get('ISU_SRT_CD', 'N/A')})")
            print(f"   Listing date: {ipo.get('LIST_DD', 'N/A')}")
            print(f"   SECUGRP_NM (industry): '{ipo.get('SECUGRP_NM', 'N/A')}'")
            print(f"   SECT_TP_NM (theme): '{ipo.get('SECT_TP_NM', 'N/A')}'")
            print(f"   MKT_TP_NM (market): '{ipo.get('MKT_TP_NM', 'N/A')}'")

        print("\n" + "-"*80)
        print("All available fields in response:")
        print("-"*80)
        if recent_ipos:
            fields = list(recent_ipos[0].keys())
            for field in sorted(fields):
                print(f"  - {field}")

        print("\n" + "-"*80)
        print("Sample full record (JSON):")
        print("-"*80)
        print(json.dumps(recent_ipos[0], indent=2, ensure_ascii=False))

    else:
        print("No 2024 IPOs found")

else:
    print(f"❌ API Error: {response.status_code}")
    print(response.text)
