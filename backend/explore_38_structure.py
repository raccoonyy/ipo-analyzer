"""
Explore 38.co.kr IPO data structure
Rate limit: Max 2 requests per second (0.5s delay between requests)
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Custom SSL adapter that allows TLSv1.2
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

print("="*80)
print("38.CO.KR IPO DATA STRUCTURE EXPLORATION")
print("="*80)
print()

# Set headers to mimic browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
}

# Create session with TLS adapter
session = requests.Session()
session.mount('https://', TLSAdapter())

# 1. Get IPO list page
print("1. Fetching IPO list page...")
list_url = "https://www.38.co.kr/html/fund/index.htm?o=k&sc=0&sw=&pg=1"

try:
    response = session.get(list_url, headers=headers, timeout=10, verify=False)
    response.encoding = 'euc-kr'  # 38.co.kr uses EUC-KR encoding

    print(f"   Status: {response.status_code}")
    print(f"   Encoding: {response.encoding}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find IPO entries
    # Look for links with pattern: ?o=v&no=XXXX
    ipo_links = []
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        if 'o=v&no=' in href:
            # Extract IPO number
            try:
                no = href.split('no=')[1].split('&')[0]
                text = link.get_text(strip=True)
                ipo_links.append({
                    'no': no,
                    'text': text,
                    'href': href
                })
            except:
                pass

    # Deduplicate by IPO number
    seen = set()
    unique_ipos = []
    for ipo in ipo_links:
        if ipo['no'] not in seen:
            seen.add(ipo['no'])
            unique_ipos.append(ipo)

    print(f"   Found {len(unique_ipos)} unique IPO entries")
    print()

    # Show first 10
    print("   Sample IPO entries:")
    for i, ipo in enumerate(unique_ipos[:10], 1):
        print(f"     {i}. No.{ipo['no']:4} - {ipo['text'][:40]}")

    print()

    # 2. Fetch detail page for first IPO
    if unique_ipos:
        first_ipo = unique_ipos[0]
        print(f"2. Fetching detail page for IPO No.{first_ipo['no']}...")
        print(f"   Waiting 0.6s (rate limit)...")
        time.sleep(0.6)

        detail_url = f"https://www.38.co.kr/html/fund/?o=v&no={first_ipo['no']}"
        detail_response = session.get(detail_url, headers=headers, timeout=10, verify=False)
        detail_response.encoding = 'euc-kr'

        print(f"   Status: {detail_response.status_code}")

        detail_soup = BeautifulSoup(detail_response.text, 'html.parser')

        # Extract all text content
        page_text = detail_soup.get_text()

        # Look for key fields
        keywords = [
            '종목코드', '기업명', '상장일',
            '공모가', '확정공모가',
            '기관경쟁률', '청약경쟁률',
            '의무보유확약', '의무보유비율',
            '균등배정', '비례배정'
        ]

        print()
        print("   Key fields found in page:")
        for keyword in keywords:
            if keyword in page_text:
                # Find context around keyword
                idx = page_text.find(keyword)
                context = page_text[max(0, idx-20):min(len(page_text), idx+100)]
                context = ' '.join(context.split())  # Clean whitespace
                print(f"     ✓ {keyword}: {context[:80]}...")
            else:
                print(f"     ✗ {keyword}: Not found")

        print()
        print("   Saving HTML to file for manual inspection...")
        with open('38_detail_sample.html', 'w', encoding='utf-8') as f:
            f.write(detail_response.text)
        print("     Saved to: 38_detail_sample.html")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("EXPLORATION COMPLETE")
print("="*80)
