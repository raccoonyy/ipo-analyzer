"""
KRX API Client
Handles API calls to KRX Data API for KOSDAQ stock information
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from src.data_collection.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class KRXApiError(Exception):
    """KRX API Error"""

    pass


class KRXApiClient:
    """
    KRX API Client for KOSDAQ data

    API Rate Limit: 10,000 requests per day per API
    """

    def __init__(self, api_key: str, timeout: int = 30, use_cache: bool = True):
        """
        Initialize KRX API Client

        Args:
            api_key: KRX API key
            timeout: Request timeout in seconds
            use_cache: Enable response caching (default: True)
        """
        self.api_key = api_key
        self.timeout = timeout
        self.use_cache = use_cache
        self.base_url = "https://data-dbg.krx.co.kr/svc/apis/sto"

        # API endpoints
        self.endpoints = {
            "stock_info": f"{self.base_url}/ksq_isu_base_info",
            "daily_trade": f"{self.base_url}/ksq_bydd_trd",
        }

        # Request counter for rate limit tracking
        self.request_count = {
            "stock_info": 0,
            "daily_trade": 0,
        }

        # Cache manager
        if use_cache:
            self.cache_manager = CacheManager()
            cache_stats = self.cache_manager.get_cache_stats()
            logger.info(f"Cache enabled: {cache_stats['cache_count']} cached responses")
        else:
            self.cache_manager = None

        logger.info("Initialized KRXApiClient")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _make_request(self, endpoint_key: str, params: Dict) -> Dict:
        """
        Make API request with retry logic

        Args:
            endpoint_key: Key for endpoint in self.endpoints
            params: Request parameters

        Returns:
            API response as dictionary

        Raises:
            KRXApiError: If API request fails
        """
        endpoint = self.endpoints[endpoint_key]

        # Check rate limit (warning at 90%)
        if self.request_count[endpoint_key] >= 9000:
            logger.warning(
                f"Approaching rate limit for {endpoint_key}: "
                f"{self.request_count[endpoint_key]}/10000 requests"
            )

        if self.request_count[endpoint_key] >= 10000:
            raise KRXApiError(
                f"Daily rate limit exceeded for {endpoint_key} (10,000 requests)"
            )

        try:
            logger.debug(f"API Request to {endpoint} with params: {params}")

            response = requests.get(
                endpoint,
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Increment request counter
            self.request_count[endpoint_key] += 1

            data = response.json()
            logger.debug(f"API Response: {len(data.get('OutBlock_1', []))} records")

            return data

        except requests.exceptions.Timeout:
            logger.error(f"API timeout: {endpoint}")
            raise KRXApiError("API 요청 시간 초과")

        except requests.exceptions.HTTPError as e:
            logger.error(f"API HTTP error: {e}")
            raise KRXApiError(f"API 오류: {e.response.status_code}")

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def get_stock_info(self, base_date: str, use_cache: bool = None) -> List[Dict]:
        """
        Get KOSDAQ stock basic information

        API: 코스닥 종목기본정보
        Endpoint: /ksq_isu_base_info

        Args:
            base_date: 기준일자 (YYYYMMDD format)
            use_cache: Override global cache setting for this request

        Returns:
            List of stock information dictionaries with keys:
            - ISU_CD: 표준코드
            - ISU_SRT_CD: 단축코드
            - ISU_NM: 한글 종목명
            - ISU_ABBRV: 한글 종목약명
            - ISU_ENG_NM: 영문 종목명
            - LIST_DD: 상장일
            - MKT_TP_NM: 시장구분
            - SECUGRP_NM: 증권구분
            - SECT_TP_NM: 소속부
            - KIND_STKCERT_TP_NM: 주식종류
            - PARVAL: 액면가
            - LIST_SHRS: 상장주식수
        """
        # Check cache
        cache_enabled = self.use_cache if use_cache is None else use_cache
        if cache_enabled and self.cache_manager:
            cache_key = self.cache_manager.generate_date_cache_key(
                "stock_info", base_date
            )
            cached_data = self.cache_manager.get(cache_key)
            if cached_data is not None:
                logger.info(f"Using cached stock info for date {base_date}")
                return cached_data

        # Fetch from API
        params = {"basDd": base_date}
        response = self._make_request("stock_info", params)

        stocks = response.get("OutBlock_1", [])
        logger.info(f"Retrieved {len(stocks)} stocks for date {base_date}")

        # Save to cache
        if cache_enabled and self.cache_manager:
            self.cache_manager.set(cache_key, stocks)

        return stocks

    def get_daily_trade_data(
        self, base_date: str, use_cache: bool = None
    ) -> List[Dict]:
        """
        Get KOSDAQ daily trading data

        API: 코스닥 일별매매정보
        Endpoint: /ksq_bydd_trd

        Args:
            base_date: 기준일자 (YYYYMMDD format)
            use_cache: Override global cache setting for this request

        Returns:
            List of trading data dictionaries with keys:
            - BAS_DD: 기준일자
            - ISU_CD: 종목코드
            - ISU_NM: 종목명
            - MKT_NM: 시장구분
            - SECT_TP_NM: 소속부
            - TDD_CLSPRC: 종가
            - CMPPREVDD_PRC: 대비
            - FLUC_RT: 등락률
            - TDD_OPNPRC: 시가
            - TDD_HGPRC: 고가
            - TDD_LWPRC: 저가
            - ACC_TRDVOL: 거래량
            - ACC_TRDVAL: 거래대금
            - MKTCAP: 시가총액
            - LIST_SHRS: 상장주식수
        """
        # Check cache
        cache_enabled = self.use_cache if use_cache is None else use_cache
        if cache_enabled and self.cache_manager:
            cache_key = self.cache_manager.generate_date_cache_key(
                "daily_trade", base_date
            )
            cached_data = self.cache_manager.get(cache_key)
            if cached_data is not None:
                logger.info(f"Using cached trade data for date {base_date}")
                return cached_data

        # Fetch from API
        params = {"basDd": base_date}
        response = self._make_request("daily_trade", params)

        trades = response.get("OutBlock_1", [])
        logger.info(f"Retrieved {len(trades)} trade records for date {base_date}")

        # Save to cache
        if cache_enabled and self.cache_manager:
            self.cache_manager.set(cache_key, trades)

        return trades

    def get_stock_info_by_code(self, base_date: str, stock_code: str) -> Optional[Dict]:
        """
        Get stock information for a specific stock code

        Args:
            base_date: 기준일자 (YYYYMMDD format)
            stock_code: 단축코드 (e.g., "123456")

        Returns:
            Stock information dictionary or None if not found
        """
        stocks = self.get_stock_info(base_date)

        for stock in stocks:
            if stock.get("ISU_SRT_CD") == stock_code:
                return stock

        logger.warning(f"Stock {stock_code} not found for date {base_date}")
        return None

    def get_daily_trade_by_code(
        self, base_date: str, stock_code: str
    ) -> Optional[Dict]:
        """
        Get daily trade data for a specific stock code

        Args:
            base_date: 기준일자 (YYYYMMDD format)
            stock_code: 종목코드

        Returns:
            Trade data dictionary or None if not found
        """
        trades = self.get_daily_trade_data(base_date)

        for trade in trades:
            # Match by ISU_CD (종목코드)
            if stock_code in trade.get("ISU_CD", ""):
                return trade

        logger.warning(f"Trade data for {stock_code} not found for date {base_date}")
        return None

    def get_ipo_stocks(self, base_date: str, listing_date: str) -> List[Dict]:
        """
        Get stocks that were listed on a specific date

        Args:
            base_date: 기준일자 (YYYYMMDD format) - date to query
            listing_date: 상장일 (YYYYMMDD format) - listing date to filter

        Returns:
            List of newly listed stocks
        """
        stocks = self.get_stock_info(base_date)

        ipo_stocks = [stock for stock in stocks if stock.get("LIST_DD") == listing_date]

        logger.info(
            f"Found {len(ipo_stocks)} IPO stocks for listing date {listing_date}"
        )

        return ipo_stocks

    def reset_request_counters(self):
        """Reset daily request counters (call at start of each day)"""
        self.request_count = {key: 0 for key in self.request_count}
        logger.info("Reset API request counters")

    def get_request_stats(self) -> Dict[str, int]:
        """Get current request statistics"""
        return self.request_count.copy()
