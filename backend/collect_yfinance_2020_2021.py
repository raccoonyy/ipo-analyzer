"""
Collect yfinance OHLCV data for 2020-2021 IPOs
Collects day0 (listing day) and day1 (next trading day) price data
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time


def get_market_suffix(code):
    """Determine market suffix for yfinance ticker"""
    # KOSDAQ codes typically start with higher numbers
    # This is a heuristic; may need manual correction
    return ".KQ"  # Default to KOSDAQ for now


def collect_ohlcv_data(code, listing_date_str):
    """
    Collect OHLCV data for IPO listing day and next trading day

    Args:
        code: Stock code (e.g., "228760")
        listing_date_str: Listing date in format "2019.03.27"

    Returns:
        dict with OHLCV data or None if failed
    """
    try:
        # Parse listing date
        listing_date = datetime.strptime(listing_date_str, "%Y.%m.%d")

        # Create ticker symbol
        suffix = get_market_suffix(code)
        ticker = f"{code}{suffix}"

        # Download data: from 1 day before listing to 7 days after
        start_date = listing_date - timedelta(days=1)
        end_date = listing_date + timedelta(days=7)

        # Get data
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)

        if len(df) == 0:
            return None

        # Find day0 (listing day) - first available data
        day0 = df.iloc[0]

        result = {
            "code": code,
            "day0_open": day0["Open"],
            "day0_high": day0["High"],
            "day0_low": day0["Low"],
            "day0_close": day0["Close"],
            "day0_volume": int(day0["Volume"]),
        }

        # Find day1 (next trading day)
        if len(df) >= 2:
            day1 = df.iloc[1]
            result["day1_high"] = day1["High"]
            result["day1_close"] = day1["Close"]
        else:
            result["day1_high"] = None
            result["day1_close"] = None

        return result

    except Exception as e:
        print(f"  Error for {code}: {e}")
        return None


def main():
    print("=" * 80)
    print("YFINANCE DATA COLLECTION FOR 2020-2021 IPOs")
    print("=" * 80)
    print()

    # Load 38.co.kr data
    df_38 = pd.read_csv("data/raw/38_2020_2021.csv")
    print(f"Total IPOs to collect: {len(df_38)}")
    print()

    collected_data = []
    success_count = 0
    fail_count = 0

    for idx, row in df_38.iterrows():
        code = str(row["code"]).zfill(6)
        listing_date = row["listing_date"]
        company_name = row["company_name"]

        print(f"[{idx+1}/{len(df_38)}] {company_name} ({code}) - {listing_date}")

        data = collect_ohlcv_data(code, listing_date)

        if data:
            collected_data.append(data)
            success_count += 1
            print(f"  ✓ Success")
        else:
            fail_count += 1
            print(f"  ✗ Failed")

        # Rate limit: wait 0.1s between requests
        time.sleep(0.1)

    print()
    print("=" * 80)
    print("COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Success: {success_count}")
    print(f"Failed:  {fail_count}")
    print(f"Success rate: {success_count/len(df_38)*100:.1f}%")
    print()

    # Save to CSV
    if collected_data:
        df_yf = pd.DataFrame(collected_data)
        output_file = "data/raw/yfinance_2020_2021.csv"
        df_yf.to_csv(output_file, index=False)

        print(f"✅ Saved to: {output_file}")
        print()
        print("Sample records:")
        print("-" * 80)
        print(df_yf.head(10).to_string())
    else:
        print("⚠️  No data collected")


if __name__ == "__main__":
    main()
