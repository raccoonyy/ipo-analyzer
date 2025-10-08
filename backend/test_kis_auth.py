"""Test KIS API authentication and show detailed error"""

import json
import traceback
from src.api.kis_client import KISApiClient

try:
    client = KISApiClient()
    print("Attempting to authenticate...")
    token = client.authenticate()
    print(f"✅ Success! Token: {token[:20]}...")

except Exception as e:
    print("❌ Authentication failed")
    print()
    print("Full error:")
    print("-" * 80)
    traceback.print_exc()
    print()

    # Try to get response details
    if hasattr(e, 'response') and e.response is not None:
        print("Response details:")
        print("-" * 80)
        print(f"Status: {e.response.status_code}")
        print(f"Headers: {dict(e.response.headers)}")
        print(f"Body: {e.response.text}")
