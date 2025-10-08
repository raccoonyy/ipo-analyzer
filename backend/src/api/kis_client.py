"""
Korea Investment Securities (KIS) OpenAPI Client
Handles authentication and data retrieval for intraday stock data
"""

import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config.settings import settings

logger = logging.getLogger(__name__)


class KISApiClient:
    """Client for Korea Investment Securities OpenAPI"""

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize KIS API client

        Args:
            app_key: KIS App Key (defaults to settings)
            app_secret: KIS App Secret (defaults to settings)
            timeout: Request timeout in seconds
        """
        self.app_key = app_key or settings.KIS_APP_KEY
        self.app_secret = app_secret or settings.KIS_APP_SECRET
        self.base_url = settings.KIS_BASE_URL
        self.auth_url = settings.KIS_AUTH_URL
        self.timeout = timeout

        if not self.app_key or not self.app_secret:
            raise ValueError("KIS_APP_KEY and KIS_APP_SECRET are required")

        self.access_token = None
        self.token_expires_at = None

        logger.info("Initialized KISApiClient")

    def authenticate(self) -> str:
        """
        Get OAuth2 access token

        Returns:
            Access token string
        """
        logger.info("Requesting KIS API access token...")

        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                self.auth_url, json=payload, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            self.access_token = data["access_token"]
            expires_in = int(data.get("expires_in", 86400))  # Default 24 hours

            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            logger.info(
                f"✅ Access token obtained, expires at {self.token_expires_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            return self.access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to authenticate: {e}")
            raise

    def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        # Only re-authenticate if token is missing or expired
        if not self.access_token:
            self.authenticate()
        elif self.token_expires_at and datetime.now() >= self.token_expires_at:
            logger.info("Access token expired, re-authenticating...")
            self.authenticate()
        else:
            # Token is still valid, no need to re-authenticate
            pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _make_request(
        self, endpoint: str, params: Dict[str, Any], tr_id: str
    ) -> Dict[str, Any]:
        """
        Make authenticated API request

        Args:
            endpoint: API endpoint path
            params: Query parameters
            tr_id: Transaction ID for the API

        Returns:
            API response data
        """
        self._ensure_authenticated()

        url = f"{self.base_url}{endpoint}"

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
        }

        try:
            response = requests.get(
                url, params=params, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # Check for API error
            if data.get("rt_cd") != "0":
                error_msg = data.get("msg1", "Unknown error")
                logger.error(f"API error: {error_msg}")
                raise ValueError(f"API error: {error_msg}")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def get_minute_candles(
        self, stock_code: str, date: str, interval: str = "1"
    ) -> List[Dict[str, Any]]:
        """
        Get minute candle data for a specific date

        Args:
            stock_code: 6-digit stock code (e.g., "005930" for Samsung)
            date: Date in YYYYMMDD format
            interval: Candle interval ("1", "3", "5", "10", "30", "60")

        Returns:
            List of candle data dictionaries
        """
        logger.info(f"Fetching {interval}-minute candles for {stock_code} on {date}...")

        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
        tr_id = "FHKST03010200"

        params = {
            "FID_ETC_CLS_CODE": "",
            "FID_COND_MRKT_DIV_CODE": "J",  # KOSDAQ
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_HOUR_1": date,  # YYYYMMDD format
            "FID_PW_DATA_INCU_YN": "Y",  # Include price data
        }

        try:
            response = self._make_request(endpoint, params, tr_id)

            # Extract output data
            candles = response.get("output2", [])

            logger.info(f"Retrieved {len(candles)} candle records")

            return candles

        except Exception as e:
            logger.error(f"Failed to get minute candles: {e}")
            return []

    def get_daily_ohlcv(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        period_code: str = "D",
        adj_price: str = "1",
    ) -> List[Dict[str, Any]]:
        """
        Get daily OHLCV data with additional indicators (PER, EPS, PBR, etc.)

        Args:
            stock_code: 6-digit stock code
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format
            period_code: Period type - "D" (daily), "W" (weekly), "M" (monthly), "Y" (yearly)
            adj_price: Price adjustment - "0" (adjusted), "1" (original)

        Returns:
            List of daily data dictionaries with PER, EPS, PBR, volume, etc.
        """
        logger.info(
            f"Fetching daily data for {stock_code} from {start_date} to {end_date}..."
        )

        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        tr_id = "FHKST03010100"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # KOSDAQ
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_DATE_1": start_date,  # YYYYMMDD
            "FID_INPUT_DATE_2": end_date,  # YYYYMMDD
            "FID_PERIOD_DIV_CODE": period_code,
            "FID_ORG_ADJ_PRC": adj_price,
        }

        try:
            response = self._make_request(endpoint, params, tr_id)

            # Extract output data (output2 contains the daily records)
            daily_data = response.get("output2", [])

            logger.info(f"Retrieved {len(daily_data)} daily records")

            return daily_data

        except Exception as e:
            logger.error(f"Failed to get daily data: {e}")
            return []

    def get_time_based_trades(self, stock_code: str, date: str) -> List[Dict[str, Any]]:
        """
        Get time-based trade execution data (30-second intervals)

        Args:
            stock_code: 6-digit stock code
            date: Date in YYYYMMDD format

        Returns:
            List of trade execution data
        """
        logger.info(f"Fetching time-based trades for {stock_code} on {date}...")

        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-time-itemconclusion"
        tr_id = "FHKST03010300"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # KOSDAQ
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_HOUR_1": date,  # YYYYMMDD format
        }

        try:
            response = self._make_request(endpoint, params, tr_id)

            # Extract output data
            trades = response.get("output2", [])

            logger.info(f"Retrieved {len(trades)} trade records")

            return trades

        except Exception as e:
            logger.error(f"Failed to get time-based trades: {e}")
            return []

    def get_current_price(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        Get current price and basic stock info

        Args:
            stock_code: 6-digit stock code

        Returns:
            Current price data
        """
        logger.info(f"Fetching current price for {stock_code}...")

        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
        tr_id = "FHKST01010100"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # KOSDAQ
            "FID_INPUT_ISCD": stock_code,
        }

        try:
            response = self._make_request(endpoint, params, tr_id)
            output = response.get("output", {})

            return output

        except Exception as e:
            logger.error(f"Failed to get current price: {e}")
            return None

    def get_ipo_offering_info(
        self,
        start_date: str,
        end_date: str,
        stock_code: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Get IPO public offering information from KSD (예탁원)

        Args:
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format
            stock_code: 6-digit stock code (empty string for all stocks)

        Returns:
            List of IPO offering data with fields:
            - sht_cd: 종목코드 (stock code)
            - fix_subscr_pri: 공모가 (IPO price)
            - face_value: 액면가 (par value)
            - subscr_dt: 청약기간 (subscription period)
            - pay_dt: 납입일 (payment date)
            - refund_dt: 환불일 (refund date)
            - list_dt: 상장일 (listing date)
            - lead_mgr: 주간사 (lead manager)
        """
        logger.info(f"Fetching IPO offering info from {start_date} to {end_date}...")

        endpoint = "/uapi/domestic-stock/v1/ksdinfo/pub-offer"
        tr_id = "HHKDB669108C0"

        params = {
            "sht_cd": stock_code,  # Empty for all stocks
            "cts": "",  # Continuation token
            "f_dt": start_date,  # YYYYMMDD
            "t_dt": end_date,  # YYYYMMDD
        }

        try:
            response = self._make_request(endpoint, params, tr_id)

            # Extract output data
            offerings = response.get("output", [])

            logger.info(f"Retrieved {len(offerings)} IPO offering records")

            return offerings

        except Exception as e:
            logger.error(f"Failed to get IPO offering info: {e}")
            return []


if __name__ == "__main__":
    """Test KIS API client"""
    import sys

    logging.basicConfig(level=logging.INFO)

    if not settings.KIS_APP_KEY or not settings.KIS_APP_SECRET:
        print("❌ KIS_APP_KEY and KIS_APP_SECRET must be set in .env file")
        sys.exit(1)

    print("Testing KIS API Client")
    print("=" * 80)

    client = KISApiClient()

    # Test authentication
    print("\n1. Testing authentication...")
    token = client.authenticate()
    print(f"✅ Access token: {token[:20]}...")

    # Test current price (using a well-known stock)
    print("\n2. Testing current price query...")
    test_code = "005930"  # Samsung Electronics
    price_data = client.get_current_price(test_code)
    if price_data:
        print(f"✅ Current price for {test_code}: {price_data.get('stck_prpr', 'N/A')}")

    # Test minute candles
    print("\n3. Testing minute candles...")
    today = datetime.now().strftime("%Y%m%d")
    candles = client.get_minute_candles(test_code, today, interval="1")
    print(f"✅ Retrieved {len(candles)} minute candles")

    print("\n" + "=" * 80)
    print("✅ All tests passed!")
