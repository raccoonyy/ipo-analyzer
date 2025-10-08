"""Find older IPOs with complete data"""

import subprocess
import time
from bs4 import BeautifulSoup

def fetch_url(url):
    """Fetch URL using curl"""
    cmd = ['curl', '-s', url]
    result = subprocess.run(cmd, capture_output=True)
    try:
        html = result.stdout.decode('euc-kr', errors='ignore')
    except:
        html = result.stdout.decode('utf-8', errors='ignore')
    return html

# Try some IPO numbers from 2024 range
test_numbers = [2000, 1900, 1800, 1700, 1600, 1500]

print("="*80)
print("FINDING OLDER IPOS WITH COMPLETE DATA")
print("="*80)
print()

for no in test_numbers:
    url = f"https://www.38.co.kr/html/fund/?o=v&no={no}"
    html = fetch_url(url)

    print(f"No.{no}: {len(html):,} bytes", end="")

    # Check if it has data
    if '해당 정보가 없습니다' in html:
        print(" - No data")
    elif len(html) < 1000:
        print(" - Too small")
    else:
        # Extract some info
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()

        # Look for key indicators
        has_code = '종목코드' in text
        has_competition = '청약경쟁률' in text
        has_listing = '상장일' in text

        indicators = []
        if has_code:
            indicators.append("종목코드✓")
        if has_competition:
            indicators.append("청약경쟁률✓")
        if has_listing:
            indicators.append("상장일✓")

        print(f" - {', '.join(indicators) if indicators else 'OK'}")

        # If looks good, save it
        if has_code and has_listing:
            with open(f'38_ipo_{no}.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"     → Saved to 38_ipo_{no}.html")

    time.sleep(0.6)  # Rate limit

print()
print("="*80)
print("SEARCH COMPLETE")
print("="*80)
