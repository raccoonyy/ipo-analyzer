"""
Collect IPO subscription data from 38.co.kr
Rate limit: Max 2 requests per second (0.6s delay)
HTML caching: Saves downloaded pages to data/cache/38_html/
"""

import sys
import subprocess
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
from datetime import datetime
from pathlib import Path


def fetch_url(url, cache_dir="data/cache/38_html"):
    """
    Fetch URL using curl with local caching

    Args:
        url: URL to fetch
        cache_dir: Directory to cache HTML files

    Returns:
        HTML content as string
    """
    # Extract IPO number from URL for cache filename
    match = re.search(r"no=(\d+)", url)
    if match:
        ipo_no = match.group(1)
        cache_path = Path(cache_dir) / f"{ipo_no}.html"

        # Check if cached file exists
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="euc-kr", errors="ignore") as f:
                    return f.read()
            except:
                # If read fails, download again
                pass

    # Download from web
    cmd = ["curl", "-s", url]
    result = subprocess.run(cmd, capture_output=True)
    try:
        html = result.stdout.decode("euc-kr", errors="ignore")
    except:
        html = result.stdout.decode("utf-8", errors="ignore")

    # Save to cache if we have IPO number
    if match and html and len(html) > 1000:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(cache_path, "w", encoding="euc-kr", errors="ignore") as f:
                f.write(html)
        except:
            # Cache write failure is not critical
            pass

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

    # 8. 청약주식수 (공모주식수)
    patterns = [
        r"청약주식수.*?<td[^>]*>\s*([0-9,]+)\s*주",  # 청약주식수
        r"공모주식수.*?<td[^>]*>\s*([0-9,]+)\s*주",  # 공모주식수
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if match:
            shares = match.group(1).replace(",", "")
            try:
                data["shares_offered"] = int(shares)
                break
            except:
                pass

    # 9. 업종 (sector/industry)
    patterns = [
        r"업종\s*</td>\s*<td[^>]*>&nbsp;\s*([가-힣A-Za-z0-9()\s,./·]+?)\s*</td>",
        r"업종.*?<td[^>]*>\s*&nbsp;\s*([가-힣A-Za-z0-9()\s,./·]+?)\s*</td>",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            sector = match.group(1).strip()
            if sector and sector != "&nbsp;":
                data["sector_38"] = sector
                break

    return data if len(data) >= 2 else None  # At least code and one other field


def is_target_year(listing_date, target_years=[2022, 2023, 2024, 2025]):
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
    print("Target years: 2022, 2023, 2024, 2025")
    print("Rate limit: 0.6s per request")
    print("HTML Cache: data/cache/38_html/")
    print()
    sys.stdout.flush()

    # IPO number range to search
    start_no = 1400
    end_no = 2350  # Full range for 2022-2025

    collected_data = []
    found_count = 0
    cache_hits = 0
    cache_misses = 0

    # Check cache directory
    cache_dir = Path("data/cache/38_html")
    existing_cache_count = (
        len(list(cache_dir.glob("*.html"))) if cache_dir.exists() else 0
    )
    print(f"Existing cached pages: {existing_cache_count}")
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

        # Check if cached before fetching
        cache_path = Path("data/cache/38_html") / f"{no}.html"
        was_cached = cache_path.exists()

        try:
            html = fetch_url(url)
            data = parse_ipo_html(html)

            # Track cache statistics
            if was_cached:
                cache_hits += 1
            else:
                cache_misses += 1

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

        # Rate limit: wait 0.6s between requests (only for web requests)
        if not was_cached:
            time.sleep(0.6)

    print()
    print("=" * 80)
    print("COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total IPOs found: {len(collected_data)}")
    print(f"Time elapsed: {(time.time() - start_time)/60:.1f} minutes")
    print()
    print("Cache Statistics:")
    print(f"  Cache hits:   {cache_hits:4} (loaded from disk)")
    print(f"  Cache misses: {cache_misses:4} (downloaded from web)")
    if cache_hits + cache_misses > 0:
        hit_rate = cache_hits / (cache_hits + cache_misses) * 100
        print(f"  Hit rate:     {hit_rate:.1f}%")
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
            "sector_38",
            "institutional_demand_rate",
            "subscription_competition_rate",
            "lockup_ratio",
            "shares_offered",
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
            "sector_38",
            "institutional_demand_rate",
            "subscription_competition_rate",
            "lockup_ratio",
            "shares_offered",
        ]:
            if col in df.columns:
                count = df[col].notna().sum()
                pct = count / len(df) * 100
                print(f"  {col:35}: {count:3} / {len(df)} ({pct:.1f}%)")

        print(f"\nYear distribution:")
        for year in [2022, 2023, 2024, 2025]:
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
