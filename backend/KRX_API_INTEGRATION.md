# KRX API 연동 가이드

## 개요

현재 백엔드는 샘플 데이터로 작동하며, 실제 IPO 데이터를 수집하려면 KRX(한국거래소) API 연동이 필요합니다.

## 필요한 작업

### 1. KRX API 조사 및 접근 권한 획득

#### 1.1 API 문서 확인
- [ ] KRX 데이터 제공 서비스 조사
  - KRX 정보데이터시스템 (http://data.krx.co.kr)
  - Open API 제공 여부 확인
  - 데이터 이용 약관 확인

#### 1.2 접근 권한 신청
- [ ] KRX API 계정 생성
- [ ] API 키 발급 신청
- [ ] 데이터 사용 승인 획득
- [ ] API 사용량 제한 확인

#### 1.3 대안 데이터 소스 검토
- [ ] 금융감독원 전자공시시스템 (DART)
- [ ] 증권사 API (한국투자증권, 키움증권 등)
- [ ] 금융 데이터 제공 업체 (FnGuide, WISEfn 등)

### 2. 필요한 데이터 엔드포인트 확인

#### 2.1 IPO 메타데이터 엔드포인트
다음 정보를 제공하는 API 엔드포인트 필요:

```
필수 필드:
- 기업명 (company_name)
- 종목코드 (code)
- 상장일 (listing_date)
- 공모가 밴드 (ipo_price_lower, ipo_price_upper)
- 확정 공모가 (ipo_price_confirmed)
- 공모주식수 (shares_offered)
- 기관경쟁률 (institutional_demand_rate)
- 의무보유확약 비율 (lockup_ratio)
- 청약경쟁률 (subscription_competition_rate)
- 납입자본금 (paid_in_capital)
- 예상 시가총액 (estimated_market_cap)
- 상장방식 (listing_method)
- 균등/비례 배정 비율 (allocation_ratio_equal/proportional)
- 업종 (industry)
- 테마 (theme)
```

#### 2.2 체결가 데이터 엔드포인트
일중 체결가 데이터를 제공하는 API 엔드포인트 필요:

```
필수 필드:
- 종목코드 (code)
- 날짜 (date)
- 시간 (time)
- 체결가 (price)
- 거래량 (volume)

데이터 빈도: 틱 단위 또는 분봉 단위
```

### 3. 코드 수정 위치

#### 3.1 IPO 메타데이터 수집
**파일**: `src/data_collection/ipo_collector.py`
**라인**: 41-146

**수정해야 할 메서드**: `collect_ipo_metadata()`

```python
def collect_ipo_metadata(self, start_year: int = 2022, end_year: int = 2025) -> pd.DataFrame:
    """
    TODO: 실제 KRX API 호출로 변경 필요

    현재: 샘플 데이터 반환
    변경 후: KRX API 호출하여 실제 IPO 데이터 수집
    """
    # 현재 코드 (Line 48-146): 샘플 데이터 생성
    # 변경 필요:
    # 1. API 엔드포인트 호출
    # 2. 응답 파싱
    # 3. DataFrame 변환
    # 4. 데이터 검증
```

#### 3.2 체결가 데이터 수집
**파일**: `src/data_collection/ipo_collector.py`
**라인**: 171-216

**수정해야 할 메서드**: `collect_intraday_prices()`

```python
def collect_intraday_prices(self, code: str, date: datetime) -> pd.DataFrame:
    """
    TODO: 실제 KRX API 호출로 변경 필요

    현재: 샘플 일중 데이터 반환
    변경 후: KRX API 호출하여 실제 체결가 데이터 수집
    """
    # 현재 코드 (Line 181-203): 샘플 데이터 생성
    # 변경 필요:
    # 1. API 엔드포인트 호출
    # 2. 날짜/종목코드로 필터링
    # 3. 응답 파싱
    # 4. DataFrame 변환
```

### 4. API 클라이언트 구현

#### 4.1 새 모듈 생성
**파일**: `src/api/krx_client.py` (신규 생성)

```python
"""
KRX API Client
실제 KRX API 호출을 담당하는 클라이언트
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime
import logging
from src.config.settings import settings

logger = logging.getLogger(__name__)


class KRXApiClient:
    """KRX API 클라이언트"""

    def __init__(self):
        self.base_url = settings.KRX_API_BASE_URL
        self.api_key = settings.KRX_API_KEY
        self.api_secret = settings.KRX_API_SECRET
        self.timeout = settings.KRX_API_TIMEOUT
        self.retry_attempts = settings.KRX_API_RETRY_ATTEMPTS

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """API 요청 실행 (인증, 재시도 로직 포함)"""
        pass

    def get_ipo_list(self, start_date: str, end_date: str) -> List[Dict]:
        """IPO 목록 조회"""
        pass

    def get_ipo_details(self, code: str) -> Dict:
        """IPO 상세 정보 조회"""
        pass

    def get_intraday_prices(self, code: str, date: str) -> List[Dict]:
        """일중 체결가 조회"""
        pass
```

#### 4.2 API 클라이언트 통합
`IPODataCollector`에서 `KRXApiClient` 사용:

```python
from src.api.krx_client import KRXApiClient

class IPODataCollector:
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        self.api_client = KRXApiClient()  # API 클라이언트 추가

    def collect_ipo_metadata(self, start_year, end_year):
        # API 클라이언트 사용하여 실제 데이터 수집
        data = self.api_client.get_ipo_list(
            start_date=f"{start_year}-01-01",
            end_date=f"{end_year}-12-31"
        )
        # ... 데이터 처리
```

### 5. 환경변수 설정

`.env` 파일에 실제 API 정보 추가:

```bash
# KRX API Configuration
KRX_API_BASE_URL=https://actual-api.krx.co.kr
KRX_API_KEY=your_actual_api_key_here
KRX_API_SECRET=your_actual_secret_here
KRX_API_TIMEOUT=30
KRX_API_RETRY_ATTEMPTS=3
```

### 6. 에러 핸들링 추가

#### 6.1 API 에러 처리
```python
class KRXApiError(Exception):
    """KRX API 에러"""
    pass

class KRXApiClient:
    def _make_request(self, endpoint, params):
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"API timeout: {endpoint}")
            raise KRXApiError("API 요청 시간 초과")
        except requests.exceptions.HTTPError as e:
            logger.error(f"API HTTP error: {e}")
            raise KRXApiError(f"API 오류: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
```

#### 6.2 재시도 로직
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(settings.KRX_API_RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def _make_request_with_retry(self, endpoint, params):
    return self._make_request(endpoint, params)
```

의존성 추가:
```bash
uv add tenacity
```

### 7. 데이터 매핑 및 변환

#### 7.1 API 응답 → DataFrame 변환
```python
def _parse_ipo_response(self, api_response: Dict) -> pd.DataFrame:
    """API 응답을 DataFrame으로 변환"""
    records = []
    for item in api_response['data']:
        record = {
            'company_name': item.get('companyName'),
            'code': item.get('stockCode'),
            'listing_date': item.get('listingDate'),
            # ... 필드 매핑
        }
        records.append(record)
    return pd.DataFrame(records)
```

#### 7.2 데이터 검증
```python
from src.validation import DataValidator

def collect_ipo_metadata(self, start_year, end_year):
    # API 호출
    df = self._fetch_from_api(start_year, end_year)

    # 데이터 검증
    is_valid, errors = DataValidator.validate_ipo_metadata(df)
    if not is_valid:
        logger.warning(f"Data validation errors: {errors}")
        # 에러 처리 (필터링 또는 예외 발생)

    return df
```

### 8. 테스트 작성

#### 8.1 Mock API 테스트
**파일**: `tests/test_krx_client.py` (신규)

```python
from unittest.mock import Mock, patch
from src.api.krx_client import KRXApiClient

def test_get_ipo_list_success():
    """IPO 목록 조회 성공 테스트"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            'data': [{'companyName': 'Test', 'stockCode': '123456'}]
        }

        client = KRXApiClient()
        result = client.get_ipo_list('2024-01-01', '2024-12-31')

        assert len(result) > 0
        assert result[0]['companyName'] == 'Test'

def test_api_timeout():
    """API 타임아웃 테스트"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout()

        client = KRXApiClient()
        with pytest.raises(KRXApiError):
            client.get_ipo_list('2024-01-01', '2024-12-31')
```

### 9. 문서화

#### 9.1 API 응답 예시 문서화
**파일**: `docs/KRX_API_RESPONSE_EXAMPLES.md` (신규)

실제 API 응답 포맷을 문서화하여 향후 유지보수 용이하게 함

#### 9.2 README 업데이트
실제 API 연동 후 README.md의 "Data Sources" 섹션 업데이트

### 10. 배포 전 체크리스트

- [ ] API 키 환경변수 설정 확인
- [ ] API 호출 제한(rate limit) 확인 및 대응
- [ ] 에러 로깅 및 모니터링 설정
- [ ] API 비용 확인 (유료 API인 경우)
- [ ] 데이터 수집 스케줄 설정
- [ ] 백업 및 복구 전략 수립

## 참고 자료

### KRX 관련 리소스
- KRX 정보데이터시스템: http://data.krx.co.kr
- 한국거래소 공식 사이트: https://www.krx.co.kr
- 금융감독원 전자공시: https://dart.fss.or.kr

### Python 라이브러리
- `requests`: HTTP 클라이언트
- `tenacity`: 재시도 로직
- `pykrx`: KRX 비공식 Python 라이브러리 (참고용)

### 현재 구현 위치
- 데이터 수집: `src/data_collection/ipo_collector.py`
- 설정: `src/config/settings.py`
- 검증: `src/validation/data_validator.py`

## 예상 소요 시간

- API 조사 및 권한 획득: **1-2주**
- API 클라이언트 구현: **3-5일**
- 테스트 및 검증: **2-3일**
- 문서화 및 배포: **1-2일**

**총 예상 기간**: 약 2-3주

## 다음 단계

1. KRX API 문서 확인 및 접근 권한 신청
2. API 엔드포인트 및 데이터 포맷 파악
3. `src/api/krx_client.py` 구현
4. 기존 `IPODataCollector` 코드 수정
5. 테스트 및 검증
6. 문서 업데이트
