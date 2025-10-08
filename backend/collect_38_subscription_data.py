"""
Collect IPO subscription data from 38.co.kr
Rate limit: Max 2 requests per second (0.6s delay)
"""

import sys
import subprocess
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
from datetime import datetime


def fetch_url(url):
    """Fetch URL using curl"""
    cmd = ["curl", "-s", url]
    result = subprocess.run(cmd, capture_output=True)
    try:
        html = result.stdout.decode("euc-kr", errors="ignore")
    except:
        html = result.stdout.decode("utf-8", errors="ignore")
    return html


def parse_ipo_html(html):
    """Parse 38.co.kr IPO HTML"""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    data = {}

    # Check if page has data
    if "해당 정보가 없습니다" in html or len(html) < 1000:
        return None

    # 1. 종목코드
    match = re.search(r"종목코드[:\s]*([A-Z0-9]{6})", text)
    if match:
        data["code"] = match.group(1)

    # 2. 종목명
    match = re.search(r"<title>IPO공모.*?>\s*([가-힣A-Za-z0-9().\s]+?)\s+공모", html)
    if match:
        data["company_name"] = match.group(1).strip()

    # 3. 상장일
    patterns = [
        r"신규상장일[^<]*?<[^>]*>([0-9.]+)",  # 신규상장일
        r"상장일</td>\s*<td[^>]*>&nbsp;\s*([0-9.]+)",  # 상장일 in table
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            listing_date = match.group(1).strip()
            data["listing_date"] = listing_date
            break

    # 4. 확정공모가
    patterns = [
        r"확정공모가\s*</td>\s*<td[^>]*>&nbsp;\s*<b>([0-9,]+)</b>",
        r"확정공모가[^<]*?<[^>]*><b>([0-9,]+)</b>",
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            ipo_price = match.group(1).replace(",", "")
            data["ipo_price"] = int(ipo_price)
            break

    # 5. 기관경쟁률
    patterns = [
        r"기관경쟁률.*?<td[^>]*>\s*([0-9,.]+):",  # Use .*? with DOTALL
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            rate = match.group(1).replace(",", "")
            try:
                data["institutional_demand_rate"] = float(rate)
                break
            except:
                pass

    # 6. 청약경쟁률 (일반)
    patterns = [
        r"청약경쟁률\s*</td>\s*<td[^>]*>&nbsp;\s*([0-9,.]+):",
        r"청약경쟁률[^<]*?<[^>]*>([0-9,.]+):",
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            rate = match.group(1).replace(",", "")
            try:
                data["subscription_competition_rate"] = float(rate)
                break
            except:
                pass

    # 7. 의무보유확약
    patterns = [
        r"의무보유확약.*?<td[^>]*>\s*([0-9,.]+)%",  # Use .*? with DOTALL
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            ratio = match.group(1).replace(",", "")
            try:
                data["lockup_ratio"] = float(ratio)
                break
            except:
                pass

    return data if len(data) >= 2 else None  # At least code and one other field


def is_target_year(listing_date, target_years=[2022, 2023, 2024]):
    """Check if listing date is in target years"""
    if not listing_date:
        return False

    # Parse date: "2023.12.04" or "23.12.04"
    try:
        parts = listing_date.split(".")
        year = int(parts[0])

        # Handle 2-digit year
        if year < 100:
            year = 2000 + year

        return year in target_years
    except:
        return False


def main():
    print("=" * 80)
    print("38.CO.KR IPO SUBSCRIPTION DATA COLLECTION")
    print("=" * 80)
    print("Target years: 2022, 2023, 2024")
    print("Rate limit: 0.6s per request")
    print()
    sys.stdout.flush()

    # IPO number range to search
    start_no = 1400
    end_no = 2300  # Full range for 2022-2024

    collected_data = []
    found_count = 0

    print(f"Searching IPO numbers {start_no} to {end_no}...")
    print()

    start_time = time.time()

    for no in range(start_no, end_no + 1):
        # Progress indicator
        if (no - start_no) % 50 == 0:
            elapsed = time.time() - start_time
            progress = (no - start_no) / (end_no - start_no) * 100
            print(
                f"Progress: {progress:.1f}% (No.{no}) - Found: {found_count} IPOs - Elapsed: {elapsed/60:.1f}min"
            )
            sys.stdout.flush()

        url = f"https://www.38.co.kr/html/fund/?o=v&no={no}"

        try:
            html = fetch_url(url)
            data = parse_ipo_html(html)

            if data and "listing_date" in data:
                # Check if it's a target year
                if is_target_year(data["listing_date"]):
                    data["ipo_no"] = no
                    collected_data.append(data)
                    found_count += 1

                    print(
                        f"  ✓ No.{no}: {data.get('company_name', 'N/A'):20} - {data.get('listing_date')} - {data.get('code', 'N/A')}"
                    )
                    sys.stdout.flush()

        except Exception as e:
            print(f"  ✗ No.{no}: Error - {e}")

        # Rate limit: wait 0.6s between requests
        time.sleep(0.6)

    print()
    print("=" * 80)
    print("COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total IPOs found: {len(collected_data)}")
    print(f"Time elapsed: {(time.time() - start_time)/60:.1f} minutes")
    print()

    if collected_data:
        # Convert to DataFrame
        df = pd.DataFrame(collected_data)

        # Filter out SPAC companies
        initial_count = len(df)
        df = df[~df["company_name"].str.contains("기업인수목적", na=False)]
        spac_count = initial_count - len(df)
        if spac_count > 0:
            print(f"Filtered out {spac_count} SPAC companies")
            print()

        # Sort by listing date
        df = df.sort_values("listing_date")

        # Reorder columns
        columns = [
            "ipo_no",
            "code",
            "company_name",
            "listing_date",
            "ipo_price",
            "institutional_demand_rate",
            "subscription_competition_rate",
            "lockup_ratio",
        ]

        # Only include columns that exist
        columns = [col for col in columns if col in df.columns]
        df = df[columns]

        # Save to CSV
        output_file = "data/raw/38_subscription_data.csv"
        df.to_csv(output_file, index=False, encoding="utf-8-sig")

        print(f"✅ Saved to: {output_file}")
        print()

        # Show statistics
        print("STATISTICS:")
        print("-" * 80)
        print(f"Total records: {len(df)}")
        print(f"\nFields coverage:")
        for col in [
            "institutional_demand_rate",
            "subscription_competition_rate",
            "lockup_ratio",
        ]:
            if col in df.columns:
                count = df[col].notna().sum()
                pct = count / len(df) * 100
                print(f"  {col:35}: {count:3} / {len(df)} ({pct:.1f}%)")

        print(f"\nYear distribution:")
        for year in [2022, 2023, 2024]:
            count = df[df["listing_date"].str.startswith(str(year))].shape[0]
            print(f"  {year}: {count} IPOs")

        print()
        print("Sample records:")
        print("-" * 80)
        print(df.head(10).to_string())
    else:
        print("⚠️  No data collected")


if __name__ == "__main__":
    main()
