"""
Collect 2025 IPO OHLCV data using yfinance
Rate limit: 1 request per second
"""

import pandas as pd
import yfinance as yf
import time
from datetime import datetime, timedelta


def get_ticker_symbol(code, market=None):
    """
    Convert Korean stock code to yfinance ticker format

    Args:
        code: 6-digit stock code
        market: 'KS' for KOSPI, 'KQ' for KOSDAQ, None for auto-detect

    Returns:
        ticker symbol (e.g., "005930.KS")
    """
    code = str(code).zfill(6)

    if market:
        return f"{code}.{market}"

    # Default to KQ (KOSDAQ) for IPOs
    return f"{code}.KQ"


def collect_yfinance_data(code, listing_date, company_name):
    """
    Collect OHLCV data for day0 and day1 using yfinance

    Args:
        code: stock code
        listing_date: listing date in YYYY-MM-DD format
        company_name: company name for logging

    Returns:
        dict with OHLCV data or None
    """
    # Try KOSDAQ first (most IPOs are on KOSDAQ)
    ticker_kq = get_ticker_symbol(code, "KQ")
    ticker_ks = get_ticker_symbol(code, "KS")

    # Parse listing date
    listing_dt = pd.to_datetime(listing_date)
    start_date = listing_dt.strftime("%Y-%m-%d")
    end_date = (listing_dt + timedelta(days=3)).strftime("%Y-%m-%d")

    # Try KOSDAQ first
    try:
        ticker = yf.Ticker(ticker_kq)
        df = ticker.history(start=start_date, end=end_date, interval="1d")

        if df.empty:
            # Try KOSPI
            ticker = yf.Ticker(ticker_ks)
            df = ticker.history(start=start_date, end=end_date, interval="1d")
            used_market = "KS"
        else:
            used_market = "KQ"

        if df.empty:
            return None

        # Extract day0 and day1 data
        result = {"market": used_market}

        if len(df) >= 1:
            day0 = df.iloc[0]
            result.update({
                "day0_open_yf": day0["Open"],
                "day0_high_yf": day0["High"],
                "day0_low_yf": day0["Low"],
                "day0_close_yf": day0["Close"],
                "day0_volume_yf": int(day0["Volume"]),
            })

        if len(df) >= 2:
            day1 = df.iloc[1]
            result.update({
                "day1_open_yf": day1["Open"],
                "day1_high_yf": day1["High"],
                "day1_low_yf": day1["Low"],
                "day1_close_yf": day1["Close"],
                "day1_volume_yf": int(day1["Volume"]),
            })

        return result

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def main():
    print("=" * 80)
    print("2025 IPO OHLCV DATA COLLECTION (yfinance)")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Rate limit: 1 request per second")
    print()

    # Load 2025 IPO dataset
    print("Loading 2025 IPO dataset...")
    df = pd.read_csv("data/raw/ipo_2025_dataset.csv")
    print(f"Total IPOs: {len(df)}")
    print()

    print("Collecting OHLCV data from yfinance...")
    print("-" * 80)
    print()

    collected_data = []
    failed_ipos = []

    for idx, row in df.iterrows():
        code = row["code"]
        company_name = row["company_name"]
        listing_date = row["listing_date"]

        print(f"[{idx+1}/{len(df)}] {company_name} ({code}) - {listing_date}")

        try:
            data = collect_yfinance_data(code, listing_date, company_name)

            if data:
                # Merge with existing row
                enhanced_row = row.to_dict()
                enhanced_row.update(data)
                collected_data.append(enhanced_row)

                day0_close = data.get("day0_close_yf", 0)
                day1_close = data.get("day1_close_yf", 0)
                market = data.get("market", "?")
                print(f"  ✓ [{market}] day0: {day0_close:,.0f}원, day1: {day1_close:,.0f}원")
            else:
                failed_ipos.append({
                    "company_name": company_name,
                    "code": code,
                    "reason": "No data available"
                })
                print(f"  ✗ No data available")

        except Exception as e:
            failed_ipos.append({
                "company_name": company_name,
                "code": code,
                "reason": str(e)
            })
            print(f"  ✗ Error: {e}")

        # Rate limit: wait 1 second between requests
        if idx < len(df) - 1:
            time.sleep(1)

        print()

    # Save results
    print("=" * 80)
    print("COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total IPOs: {len(df)}")
    print(f"Successfully collected: {len(collected_data)}")
    print(f"Failed: {len(failed_ipos)}")
    print()

    if collected_data:
        # Save enhanced dataset
        df_enhanced = pd.DataFrame(collected_data)
        output_file = "data/raw/ipo_2025_dataset_yfinance.csv"
        df_enhanced.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"✅ Saved to: {output_file}")
        print()

        # Show statistics
        print("STATISTICS:")
        print("-" * 80)

        # Market distribution
        if "market" in df_enhanced.columns:
            market_counts = df_enhanced["market"].value_counts()
            print("Market distribution:")
            for market, count in market_counts.items():
                print(f"  {market}: {count} IPOs")
            print()

        # Data completeness
        has_day0 = df_enhanced["day0_close_yf"].notna().sum()
        has_day1 = df_enhanced["day1_close_yf"].notna().sum()
        print(f"Data completeness:")
        print(f"  Day0 data: {has_day0}/{len(df_enhanced)} ({has_day0/len(df_enhanced)*100:.1f}%)")
        print(f"  Day1 data: {has_day1}/{len(df_enhanced)} ({has_day1/len(df_enhanced)*100:.1f}%)")
        print()

        # Sample records
        print("Sample records (first 10):")
        print("-" * 80)
        cols_to_show = [
            "company_name",
            "code",
            "listing_date",
            "ipo_price_confirmed",
            "day0_close_yf",
            "day1_close_yf",
        ]
        print(df_enhanced[cols_to_show].head(10).to_string(index=False))

    if failed_ipos:
        print()
        print("Failed IPOs:")
        print("-" * 80)
        for ipo in failed_ipos:
            print(
                f"  - {ipo.get('company_name', 'N/A')} ({ipo.get('code', 'N/A')}): {ipo.get('reason', 'Unknown error')}"
            )


if __name__ == "__main__":
    main()
