"""
Explore 38.co.kr IPO data structure using curl
Rate limit: Max 2 requests per second (0.5s delay between requests)
"""

import subprocess
from bs4 import BeautifulSoup
import time
import re

print("="*80)
print("38.CO.KR IPO DATA STRUCTURE EXPLORATION (using curl)")
print("="*80)
print()

def fetch_url(url):
    """Fetch URL using curl"""
    cmd = [
        'curl',
        '-s',  # Silent mode
        '-L',  # Follow redirects
        '--compressed',  # Handle gzip/deflate
        url
    ]

    result = subprocess.run(cmd, capture_output=True)

    # Decode from EUC-KR
    try:
        html = result.stdout.decode('euc-kr')
    except:
        html = result.stdout.decode('utf-8', errors='ignore')

    return html

# 1. Get IPO list page
print("1. Fetching IPO list page...")
list_url = "https://www.38.co.kr/html/fund/index.htm?o=k&sc=0&sw=&pg=1"

html = fetch_url(list_url)
print(f"   Fetched {len(html)} bytes")

soup = BeautifulSoup(html, 'html.parser')

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
    detail_html = fetch_url(detail_url)

    print(f"   Fetched {len(detail_html)} bytes")

    detail_soup = BeautifulSoup(detail_html, 'html.parser')

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
        f.write(detail_html)
    print("     Saved to: 38_detail_sample.html")

    # Try to extract structured data
    print()
    print("3. Extracting structured data...")

    # Look for tables
    tables = detail_soup.find_all('table')
    print(f"   Found {len(tables)} tables")

    # Look for specific patterns in text
    patterns = {
        '종목코드': r'종목코드[:\s]*([A-Z0-9]+)',
        '공모가': r'확정공모가[:\s]*([\d,]+)',
        '기관경쟁률': r'기관경쟁률[:\s]*([\d,.]+)',
        '청약경쟁률': r'청약경쟁률[:\s]*([\d,.]+)',
        '의무보유비율': r'의무보유[^:\n]*([\d.]+)%',
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, page_text)
        if match:
            print(f"     ✓ {field}: {match.group(1)}")
        else:
            print(f"     ✗ {field}: Pattern not found")

print()
print("="*80)
print("EXPLORATION COMPLETE")
print("="*80)
