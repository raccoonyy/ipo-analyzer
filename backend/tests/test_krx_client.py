"""
Tests for KRX API Client
"""

import pytest
from unittest.mock import Mock, patch
from src.api.krx_client import KRXApiClient, KRXApiError


def test_krx_client_initialization():
    """Test KRX client initialization"""
    client = KRXApiClient(api_key="test_key", timeout=30)

    assert client.api_key == "test_key"
    assert client.timeout == 30
    assert "stock_info" in client.endpoints
    assert "daily_trade" in client.endpoints


def test_get_headers():
    """Test API headers generation"""
    client = KRXApiClient(api_key="test_key")
    headers = client._get_headers()

    assert headers["Authorization"] == "Bearer test_key"
    assert headers["Content-Type"] == "application/json"


@patch("requests.get")
def test_get_stock_info_success(mock_get):
    """Test successful stock info retrieval"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "OutBlock_1": [
            {
                "ISU_CD": "KR123456",
                "ISU_SRT_CD": "123456",
                "ISU_NM": "테스트기업",
                "LIST_DD": "20240101",
                "LIST_SHRS": "1000000",
                "PARVAL": "5000",
            }
        ]
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    client = KRXApiClient(api_key="test_key")
    stocks = client.get_stock_info("20240101")

    assert len(stocks) == 1
    assert stocks[0]["ISU_NM"] == "테스트기업"
    mock_get.assert_called_once()


@patch("requests.get")
def test_get_daily_trade_data_success(mock_get):
    """Test successful daily trade data retrieval"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "OutBlock_1": [
            {
                "BAS_DD": "20240101",
                "ISU_CD": "KR123456",
                "ISU_NM": "테스트기업",
                "TDD_CLSPRC": "50000",
                "TDD_HGPRC": "52000",
                "TDD_LWPRC": "49000",
                "ACC_TRDVOL": "1000000",
            }
        ]
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    client = KRXApiClient(api_key="test_key")
    trades = client.get_daily_trade_data("20240101")

    assert len(trades) == 1
    assert trades[0]["TDD_CLSPRC"] == "50000"
    assert trades[0]["TDD_HGPRC"] == "52000"


@patch("requests.get")
def test_api_timeout_error(mock_get):
    """Test API timeout handling"""
    import requests
    from tenacity import RetryError

    mock_get.side_effect = requests.exceptions.Timeout()

    client = KRXApiClient(api_key="test_key")

    # Retry logic wraps the error in RetryError
    with pytest.raises(RetryError):
        client.get_stock_info("20240101")


@patch("requests.get")
def test_api_http_error(mock_get):
    """Test API HTTP error handling"""
    import requests
    from tenacity import RetryError

    mock_response = Mock()
    mock_response.status_code = 500
    mock_get.side_effect = requests.exceptions.HTTPError(response=mock_response)

    client = KRXApiClient(api_key="test_key")

    # Retry logic wraps the error in RetryError
    with pytest.raises(RetryError):
        client.get_stock_info("20240101")


def test_rate_limit_tracking():
    """Test rate limit tracking"""
    client = KRXApiClient(api_key="test_key")

    initial_count = client.request_count["stock_info"]
    assert initial_count == 0

    stats = client.get_request_stats()
    assert stats["stock_info"] == 0

    # Test reset
    client.request_count["stock_info"] = 100
    client.reset_request_counters()
    assert client.request_count["stock_info"] == 0


@patch("requests.get")
def test_rate_limit_exceeded(mock_get):
    """Test rate limit exceeded error"""
    from tenacity import RetryError

    client = KRXApiClient(api_key="test_key")
    client.request_count["stock_info"] = 10000

    # Rate limit check happens before retry, so it raises RetryError
    with pytest.raises(RetryError):
        client.get_stock_info("20240101")


@patch("requests.get")
def test_get_stock_info_by_code(mock_get):
    """Test getting stock info by code"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "OutBlock_1": [
            {"ISU_SRT_CD": "123456", "ISU_NM": "기업A"},
            {"ISU_SRT_CD": "789012", "ISU_NM": "기업B"},
        ]
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    client = KRXApiClient(api_key="test_key")
    stock = client.get_stock_info_by_code("20240101", "123456")

    assert stock is not None
    assert stock["ISU_NM"] == "기업A"

    # Test not found
    stock_not_found = client.get_stock_info_by_code("20240101", "999999")
    assert stock_not_found is None
