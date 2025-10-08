"""
Test KIS API Historical Intraday Data Capability

This script tests whether KIS API can fetch historical minute-level data
for IPOs from different time periods:
- 2025 IPO (recent)
- 2024 IPO (older than 30 days)
- 2022 IPO (2-3 years old)

This will determine if KIS API has retention limits like yfinance (30 days).
"""

import logging
from datetime import datetime
from src.api.kis_client import KISApiClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def test_historical_intraday(client, company_name, stock_code, listing_date_str):
    """Test intraday data retrieval for a specific IPO"""
    print("\n" + "=" * 80)
    print(f"Testing: {company_name} ({stock_code})")
    print(f"Listing Date: {listing_date_str}")
    print("=" * 80)

    # Convert date to YYYYMMDD format
    date_obj = datetime.strptime(listing_date_str, "%Y-%m-%d")
    date_yyyymmdd = date_obj.strftime("%Y%m%d")

    # Calculate days ago
    days_ago = (datetime.now() - date_obj).days
    print(f"Days since listing: {days_ago}")
    print()

    # Test different intervals
    intervals = ["1", "5", "30", "60"]

    for interval in intervals:
        print(f"Testing {interval}-minute candles...")
        try:
            candles = client.get_minute_candles(stock_code, date_yyyymmdd, interval=interval)

            if candles:
                print(f"✅ SUCCESS: Retrieved {len(candles)} candle records")

                # Show sample data
                if len(candles) > 0:
                    sample = candles[0]
                    print(f"   Sample data: {sample}")
            else:
                print(f"❌ EMPTY: No data returned (empty list)")

        except Exception as e:
            print(f"❌ ERROR: {e}")

        print()


def main():
    """Test KIS API historical intraday data capability"""
    print("=" * 80)
    print("KIS API HISTORICAL INTRADAY DATA TEST")
    print("=" * 80)
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Initialize KIS API client
    print("Initializing KIS API client...")
    try:
        client = KISApiClient()
        print("✅ Client initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return

    # Test cases: IPOs from different time periods
    test_cases = [
        # Recent 2025 IPO (likely within 30 days if today is early 2025)
        {
            "company_name": "명인제약",
            "stock_code": "317450",
            "listing_date": "2025-09-24",
        },
        # 2024 IPO (older than 30 days)
        {
            "company_name": "파인메딕스",
            "stock_code": "387570",
            "listing_date": "2024-12-26",
        },
        # 2022 IPO (2-3 years old)
        {
            "company_name": "루닛",
            "stock_code": "328130",
            "listing_date": "2022-07-21",
        },
    ]

    results = []

    for test_case in test_cases:
        result = test_historical_intraday(
            client,
            test_case["company_name"],
            test_case["stock_code"],
            test_case["listing_date"],
        )
        results.append(result)

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    print("Key Findings:")
    print("- If all tests return data: KIS API has NO retention limit ✅")
    print("- If only recent data works: KIS API has retention limit like yfinance ❌")
    print("- If no data works: API configuration issue or endpoint limitation ⚠️")
    print()
    print("Next steps based on results:")
    print("1. ✅ No retention limit → Proceed with KIS API for historical intraday collection")
    print("2. ❌ Has retention limit → Only collect new IPOs going forward")
    print("3. ⚠️ Configuration issue → Check API credentials and market code settings")
    print()


if __name__ == "__main__":
    main()
