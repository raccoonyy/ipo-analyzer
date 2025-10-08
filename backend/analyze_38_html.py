"""Analyze saved 38.co.kr HTML"""

from bs4 import BeautifulSoup
import re

with open('38_ipo_2234.html', 'r', encoding='euc-kr', errors='ignore') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
text = soup.get_text()

print("="*80)
print("38.CO.KR IPO PAGE ANALYSIS (No.2234)")
print("="*80)
print()

# Look for key fields
keywords = ['종목코드', '기업명', '상장일', '공모가', '확정공모가', '기관경쟁률', '청약경쟁률', '의무보유', '균등배정', '비례배정']

print("1. KEYWORD SEARCH:")
print("-"*80)
for keyword in keywords:
    if keyword in text:
        idx = text.find(keyword)
        context = text[max(0, idx-10):min(len(text), idx+100)]
        context = ' '.join(context.split())
        print(f"✓ {keyword:12}: {context[:90]}")
    else:
        print(f"✗ {keyword:12}: Not found")

print()
print("2. PATTERN MATCHING:")
print("-"*80)

patterns = {
    '종목코드': r'종목코드[:\s]*([A-Z0-9]{6})',
    '공모가': r'확정공모가[:\s]*([\d,]+)\s*원',
    '상장일': r'상장[예정]*일[:\s]*([\d.년월일\s]+)',
    '기관경쟁률': r'기관경쟁률[:\s]*([\d,.]+)\s*[:대]',
    '청약경쟁률': r'청약경쟁률[:\s]*([\d,.]+)\s*[:대]',
    '의무보유비율': r'의무보유[^:\n]*([\d.]+)%',
}

for field, pattern in patterns.items():
    match = re.search(pattern, text)
    if match:
        print(f"✓ {field:12}: {match.group(1)}")
    else:
        # Try broader pattern
        if field in text:
            idx = text.find(field)
            snippet = text[idx:idx+200]
            print(f"? {field:12}: {' '.join(snippet.split())[:80]}...")
        else:
            print(f"✗ {field:12}: Not found")

print()
print("3. TABLE ANALYSIS:")
print("-"*80)

tables = soup.find_all('table')
print(f"Found {len(tables)} tables")

for i, table in enumerate(tables[:5], 1):
    rows = table.find_all('tr')
    print(f"\nTable {i}: {len(rows)} rows")
    # Show first few rows
    for j, row in enumerate(rows[:3], 1):
        cells = row.find_all(['td', 'th'])
        if cells:
            row_text = ' | '.join([c.get_text(strip=True)[:30] for c in cells[:5]])
            print(f"  Row {j}: {row_text}")

print()
print("4. SAVE CLEANED TEXT:")
print("-"*80)

with open('38_ipo_2234_text.txt', 'w', encoding='utf-8') as f:
    f.write(text)

print("Saved cleaned text to: 38_ipo_2234_text.txt")
