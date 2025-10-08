"""
Temporary script to test KRX API directly
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Get API key
api_key = os.getenv("KRX_API_KEY")

# Call API
base_date = "20241231"
endpoint = "https://data-dbg.krx.co.kr/svc/apis/sto/ksq_isu_base_info"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

params = {"basDd": base_date}

print("=" * 80)
print(f"KRX API 호출: 코스닥 종목기본정보")
print(f"Endpoint: {endpoint}")
print(f"기준일자: {base_date}")
print("=" * 80)
print()

response = requests.get(endpoint, params=params, headers=headers, timeout=30)
response.raise_for_status()

data = response.json()
stocks = data.get("OutBlock_1", [])

print(f"총 조회된 종목 수: {len(stocks)}")
print()

# Show first 3 records
print("=" * 80)
print("샘플 데이터 (첫 3개 종목):")
print("=" * 80)
for i, stock in enumerate(stocks[:3], 1):
    print(f"\n{i}. 종목명: {stock.get('ISU_NM', 'N/A')}")
    print(f"   종목코드: {stock.get('ISU_SRT_CD', 'N/A')}")
    print(f"   상장일: {stock.get('LIST_DD', 'N/A')}")
    print(f"   증권구분(SECUGRP_NM): {stock.get('SECUGRP_NM', 'N/A')}")
    print(f"   소속부(SECT_TP_NM): {stock.get('SECT_TP_NM', 'N/A')}")
    print(f"   시장구분: {stock.get('MKT_TP_NM', 'N/A')}")
    print(f"   액면가: {stock.get('PARVAL', 'N/A')}")
    print(f"   상장주식수: {stock.get('LIST_SHRS', 'N/A')}")

print()
print("=" * 80)
print("전체 응답 필드 목록:")
print("=" * 80)
if stocks:
    print(", ".join(stocks[0].keys()))

print()
print("=" * 80)
print("2022-2024 상장 IPO 필터링:")
print("=" * 80)

# Filter IPOs from 2022-2024
ipos = []
for stock in stocks:
    list_date = stock.get("LIST_DD", "")
    if list_date and (
        list_date.startswith("2022")
        or list_date.startswith("2023")
        or list_date.startswith("2024")
    ):
        ipos.append(stock)

print(f"2022-2024 상장 종목 수: {len(ipos)}")
print()

# Show recent 10 IPOs
print("최근 10개 IPO:")
print("-" * 80)
for ipo in sorted(ipos, key=lambda x: x.get("LIST_DD", ""), reverse=True)[:10]:
    print(
        f'{ipo.get("ISU_NM", "N/A"):30} | 상장일: {ipo.get("LIST_DD", "N/A")} | 증권: {ipo.get("SECUGRP_NM", "N/A"):10} | 소속: {ipo.get("SECT_TP_NM", "N/A")}'
    )

print()
print("=" * 80)
print("증권구분(SECUGRP_NM) 분포:")
print("=" * 80)

# Count SECUGRP_NM
secugrp_count = {}
for ipo in ipos:
    secugrp = ipo.get("SECUGRP_NM", "N/A")
    secugrp_count[secugrp] = secugrp_count.get(secugrp, 0) + 1

for secugrp, count in sorted(secugrp_count.items(), key=lambda x: x[1], reverse=True):
    print(f"{secugrp:20}: {count:3}개 ({count/len(ipos)*100:.1f}%)")

print()
print("=" * 80)
print("소속부(SECT_TP_NM) 분포 (상위 15개):")
print("=" * 80)

# Count SECT_TP_NM
sect_count = {}
for ipo in ipos:
    sect = ipo.get("SECT_TP_NM", "N/A")
    sect_count[sect] = sect_count.get(sect, 0) + 1

for sect, count in sorted(sect_count.items(), key=lambda x: x[1], reverse=True)[:15]:
    print(f"{sect:35}: {count:3}개 ({count/len(ipos)*100:.1f}%)")

print()
print("=" * 80)
print("상세 예시 (최근 IPO 5개):")
print("=" * 80)

import json

for i, ipo in enumerate(
    sorted(ipos, key=lambda x: x.get("LIST_DD", ""), reverse=True)[:5], 1
):
    print(f"\n{i}. {ipo.get('ISU_NM', 'N/A')}")
    print(json.dumps(ipo, indent=2, ensure_ascii=False))
