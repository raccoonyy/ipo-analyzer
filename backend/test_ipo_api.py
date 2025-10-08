"""Test KIS IPO offering API to see actual response structure"""

import json
from src.api.kis_client import KISApiClient

client = KISApiClient()

# Test with recent date range
print("Testing IPO Offering API...")
print("=" * 80)

result = client.get_ipo_offering_info(
    start_date="20240101",
    end_date="20241231",
    stock_code=""
)

print(f"Type: {type(result)}")
print(f"Length: {len(result)}")
print()

if result:
    print("First record:")
    print(json.dumps(result[0], indent=2, ensure_ascii=False))
else:
    print("Empty result - checking raw API response...")

    # Make raw request to see actual response
    import requests

    client.authenticate()

    endpoint = "/uapi/domestic-stock/v1/ksdinfo/pub-offer"
    url = f"{client.base_url}{endpoint}"

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "authorization": f"Bearer {client.access_token}",
        "appkey": client.app_key,
        "appsecret": client.app_secret,
        "tr_id": "HHKDB669108C0",
    }

    params = {
        "sht_cd": "",
        "cts": "",
        "f_dt": "20240101",
        "t_dt": "20241231",
    }

    print("\nRaw API request:")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print()

    response = requests.get(url, params=params, headers=headers, timeout=30)

    print(f"Status: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
