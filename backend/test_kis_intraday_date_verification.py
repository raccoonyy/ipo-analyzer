"""
Verify KIS API Intraday Data Date

This script checks if the data returned by KIS API is actually from the requested
historical date or if it's just returning current/recent data.
"""

import logging
from datetime import datetime
from src.api.kis_client import KISApiClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Verify data dates returned by KIS API"""
    print("=" * 80)
    print("KIS API INTRADAY DATA DATE VERIFICATION")
    print("=" * 80)
    print()

    client = KISApiClient()

    # Test with a 2022 IPO - Luneit (루닛)
    company = "루닛"
    stock_code = "328130"
    listing_date = "2022-07-21"

    print(f"Company: {company}")
    print(f"Stock Code: {stock_code}")
    print(f"Listing Date: {listing_date}")
    print(f"Requested Date: {listing_date} (converted to 20220721)")
    print()

    # Fetch 1-minute candles for the listing date
    date_yyyymmdd = "20220721"
    print(f"Fetching 1-minute candles for date: {date_yyyymmdd}...")
    candles = client.get_minute_candles(stock_code, date_yyyymmdd, interval="1")

    print(f"Retrieved {len(candles)} records")
    print()

    if candles:
        print("Analyzing returned data...")
        print("=" * 80)

        # Check first 5 records
        for i, candle in enumerate(candles[:5], 1):
            business_date = candle.get('stck_bsop_date', 'N/A')
            candle_hour = candle.get('stck_cntg_hour', 'N/A')
            price = candle.get('stck_prpr', 'N/A')
            volume = candle.get('cntg_vol', 'N/A')

            print(f"Record {i}:")
            print(f"  Business Date (stck_bsop_date): {business_date}")
            print(f"  Candle Hour (stck_cntg_hour): {candle_hour}")
            print(f"  Price: {price}")
            print(f"  Volume: {volume}")
            print()

        # Check if all records have the same business date
        unique_dates = set(c.get('stck_bsop_date') for c in candles)
        print(f"Unique business dates in response: {unique_dates}")
        print()

        # Verification
        print("=" * 80)
        print("VERIFICATION RESULTS")
        print("=" * 80)

        requested_date = date_yyyymmdd
        actual_dates = list(unique_dates)

        if len(actual_dates) == 1 and actual_dates[0] == requested_date:
            print(f"✅ SUCCESS: API returned data for requested date {requested_date}")
            print(f"   KIS API can retrieve historical intraday data!")
        elif len(actual_dates) == 1:
            print(f"❌ MISMATCH: API returned data for {actual_dates[0]}")
            print(f"   Requested: {requested_date}")
            print(f"   Received: {actual_dates[0]}")
            print()
            print("⚠️  KIS API appears to ignore the historical date parameter")
            print("   and returns current/recent data instead.")
            print()

            # Check if it's today's data
            today = datetime.now().strftime("%Y%m%d")
            if actual_dates[0] == today:
                print(f"   The returned data is from TODAY ({today})")
            else:
                print(f"   The returned data is from {actual_dates[0]}")
        else:
            print(f"⚠️  WARNING: Multiple dates found in response: {actual_dates}")
    else:
        print("❌ No data returned")

    print()
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    print("If requested date != returned date:")
    print("  → KIS API cannot fetch historical intraday data")
    print("  → Similar limitation to yfinance (but different mechanism)")
    print("  → Can only collect intraday data for current/recent dates")
    print()


if __name__ == "__main__":
    main()
