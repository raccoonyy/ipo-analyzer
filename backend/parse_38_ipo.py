"""Parse detailed IPO data from 38.co.kr HTML"""

from bs4 import BeautifulSoup
import re

def parse_ipo_html(filename):
    """Parse 38.co.kr IPO HTML file"""

    with open(filename, 'r', encoding='euc-kr', errors='ignore') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()

    data = {}

    # 1. 종목코드
    match = re.search(r'종목코드[:\s]*([A-Z0-9]{6})', text)
    if match:
        data['stock_code'] = match.group(1)

    # 2. 기업명 (회사명)
    match = re.search(r'기업명[:\s]*([가-힣A-Za-z0-9().,\s]+?)(?:\n|기업구분|종목코드)', text)
    if not match:
        # Try company name from title or other location
        match = re.search(r'<title>([가-힣A-Za-z0-9().,\s]+?)\s*[-|]', html)
    if match:
        data['company_name'] = match.group(1).strip()

    # 3. 상장일
    match = re.search(r'상장[예정]*일[:\s]*([\d.년월일]+)', text)
    if match:
        listing_date = match.group(1)
        # Clean up format: "2024.05.23" or "24.05.23"
        listing_date = re.sub(r'년|월|일', '', listing_date).strip()
        data['listing_date'] = listing_date

    # 4. 확정공모가
    match = re.search(r'확정공모가[:\s]*([\d,]+)\s*원', text)
    if match:
        ipo_price = match.group(1).replace(',', '')
        data['ipo_price'] = int(ipo_price)

    # 5. 기관경쟁률
    patterns = [
        r'기관경쟁률[:\s]*([\d,]+\.?\d*)\s*:',  # "기관경쟁률 1234.56:"
        r'기관경쟁률[:\s]*([\d,]+\.?\d*)\s*대',  # "기관경쟁률 1234.56대"
        r'기관경쟁률[:\s]*([\d,]+\.?\d*)',       # "기관경쟁률 1234.56"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            rate = match.group(1).replace(',', '')
            try:
                data['institutional_demand_rate'] = float(rate)
                break
            except:
                pass

    # 6. 청약경쟁률 (일반 청약)
    patterns = [
        r'일반청약[:\s]*([\d,]+\.?\d*)\s*:',
        r'일반청약[:\s]*([\d,]+\.?\d*)\s*대',
        r'청약경쟁률[:\s]*(?:일반\s*)*([\d,]+\.?\d*)\s*:',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            rate = match.group(1).replace(',', '')
            try:
                data['subscription_competition_rate'] = float(rate)
                break
            except:
                pass

    # 7. 의무보유비율
    patterns = [
        r'의무보유확약[:\s]*([\d,]+\.?\d*)\s*%',
        r'의무보유[^:\n]{0,20}([\d,]+\.?\d*)\s*%',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            ratio = match.group(1).replace(',', '')
            try:
                data['lockup_ratio'] = float(ratio)
                break
            except:
                pass

    return data


# Test parsing
print("="*80)
print("PARSING 38.CO.KR IPO DATA")
print("="*80)
print()

files = [
    '38_ipo_2000.html',
    '38_ipo_1900.html',
    '38_ipo_1800.html',
]

for filename in files:
    print(f"Parsing: {filename}")
    print("-"*80)

    try:
        data = parse_ipo_html(filename)

        for key, value in data.items():
            print(f"  {key:30}: {value}")

        print()

    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        print()

print("="*80)
print("PARSING COMPLETE")
print("="*80)
