"""Test KIS daily API to see all available fields"""

import json
from src.api.kis_client import KISApiClient
import time

client = KISApiClient()

# Use a known stock that IPO'd recently
stock_code = "420770"  # 기가비스
listing_date = "20220829"  # Listing date

print("=" * 80)
print(f"Testing daily price API for {stock_code} (기가비스)")
print("=" * 80)
print()

# Wait to avoid rate limit
time.sleep(2)

# Get daily data around listing date
result = client.get_daily_ohlcv(
    stock_code=stock_code,
    start_date=listing_date,
    end_date=listing_date,
)

print(f"Number of records: {len(result)}")
print()

if result:
    print("All fields in first record:")
    print("=" * 80)

    record = result[0]
    for key, value in sorted(record.items()):
        print(f"{key:30}: {value}")

    print()
    print("=" * 80)
    print("Looking for IPO price related fields...")
    print("=" * 80)

    # Look for potential IPO price fields
    keywords = ['offer', 'ipo', 'pub', 'subscr', 'issue', 'fix', 'pri']

    matching_fields = []
    for key in record.keys():
        key_lower = key.lower()
        if any(kw in key_lower for kw in keywords):
            matching_fields.append((key, record[key]))

    if matching_fields:
        print("\nPotential IPO price fields:")
        for key, value in matching_fields:
            print(f"  {key:30}: {value}")
    else:
        print("\nNo IPO price related fields found")
else:
    print("No data returned")
