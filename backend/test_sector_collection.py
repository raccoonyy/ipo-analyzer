"""
Test sector collection from 38.co.kr
"""

import subprocess
from bs4 import BeautifulSoup
import re


def fetch_url(url):
    """Fetch URL using curl"""
    cmd = ["curl", "-s", url]
    result = subprocess.run(cmd, capture_output=True)
    try:
        html = result.stdout.decode("euc-kr", errors="ignore")
    except:
        html = result.stdout.decode("utf-8", errors="ignore")
    return html


def parse_sector(html):
    """Parse sector from HTML"""
    # 업종 (sector/industry)
    patterns = [
        r"업종\s*</td>\s*<td[^>]*>&nbsp;\s*([가-힣A-Za-z0-9()\s,./·]+?)\s*</td>",
        r"업종.*?<td[^>]*>\s*&nbsp;\s*([가-힣A-Za-z0-9()\s,./·]+?)\s*</td>",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            sector = match.group(1).strip()
            if sector and sector != "&nbsp;":
                return sector
    return None


# Test on 3 IPOs
test_nos = [2220, 1780, 2100]  # 명인제약, 위니아에어컨, random

for no in test_nos:
    url = f"https://www.38.co.kr/html/fund/?o=v&no={no}"
    html = fetch_url(url)
    sector = parse_sector(html)

    # Get company name
    match = re.search(r"<title>IPO공모.*?>\s*([가-힣A-Za-z0-9().\s]+?)\s+공모", html)
    company = match.group(1).strip() if match else "Unknown"

    print(f"No.{no} - {company:20} -> {sector}")
