# KRX API 연동 완료 ✅

## 구현 사항

### 1. KRX API 클라이언트 (`src/api/krx_client.py`)

KRX 데이터 API를 호출하는 클라이언트를 구현했습니다.

**지원하는 API:**
- `코스닥 종목기본정보` - 종목 메타데이터 조회
- `코스닥 일별매매정보` - 일별 시가/고가/저가/종가 조회

**주요 기능:**
- ✅ API 인증 (Authorization Bearer 토큰)
- ✅ 재시도 로직 (tenacity 사용, 최대 3회)
- ✅ Rate Limit 추적 (API당 하루 10,000건)
- ✅ 에러 처리 (Timeout, HTTPError 등)
- ✅ 실제 데이터 테스트 완료

**주요 메서드:**
```python
client = KRXApiClient(api_key="your_key")

# 종목 정보 조회
stocks = client.get_stock_info(base_date="20240101")

# 일별 매매 정보 조회
trades = client.get_daily_trade_data(base_date="20240101")

# 특정 종목 조회
stock = client.get_stock_info_by_code("20240101", "123456")

# IPO 종목 필터링
ipo_stocks = client.get_ipo_stocks(base_date="20241231", listing_date="20241201")
```

### 2. IPODataCollector 업데이트

KRX API를 사용하도록 데이터 수집 모듈을 업데이트했습니다.

**사용 방법:**
```python
# 샘플 데이터 사용 (API 키 불필요)
collector = IPODataCollector(use_sample_data=True)
df = collector.collect_ipo_metadata(2022, 2025)

# KRX API 사용 (API 키 필요)
collector = IPODataCollector(use_sample_data=False)
df = collector.collect_ipo_metadata(2022, 2025)
```

**자동 처리:**
- API 키가 없으면 자동으로 샘플 데이터로 폴백
- 환경변수 `KRX_API_KEY`에서 API 키 로드

### 3. 환경 변수 설정

`.env` 파일에 다음 변수 추가:
```bash
KRX_API_KEY=your_api_key_here
KRX_API_TIMEOUT=30
KRX_API_RATE_LIMIT=10000
```

### 4. 테스트

새로운 테스트 추가: `tests/test_krx_client.py`
- 총 9개 테스트 (모두 통과)
- API 호출, 에러 처리, Rate Limit 등 검증

## 제한 사항

### KRX API에서 제공하지 않는 데이터

다음 IPO 특화 데이터는 KRX API에서 제공하지 않습니다:
- ❌ 공모가 밴드 (ipo_price_lower, ipo_price_upper)
- ❌ 확정 공모가 (ipo_price_confirmed)
- ❌ 기관경쟁률 (institutional_demand_rate)
- ❌ 의무보유확약 비율 (lockup_ratio)
- ❌ 청약경쟁률 (subscription_competition_rate)
- ❌ 균등/비례 배정 비율 (allocation_ratio_equal/proportional)

**현재 대응:**
- 액면가(PARVAL)를 공모가 대용으로 사용
- 기타 필드는 기본값(0 또는 50) 설정

**향후 대응 방안:**
1. 금융감독원 DART API 연동 (공시 정보)
2. 증권사 API 활용 (한국투자증권 등)
3. 수동 데이터 입력 기능 추가

### 일중 데이터

KRX API는 일별 데이터만 제공합니다:
- ✅ 시가, 고가, 저가, 종가 (일별)
- ❌ 틱/분봉 데이터 (일중)

**현재 대응:**
- 일별 고가를 Day 0 High로 사용
- 일별 종가를 Day 0 Close로 사용

**향후 대응:**
- 한국투자증권 API 연동 (일중 데이터 제공 예정)

## 다음 단계

### 1. 한국투자 API 연동 (일중 데이터)
- [ ] 한국투자 API 클라이언트 구현
- [ ] 일중 틱/분봉 데이터 수집
- [ ] IPODataCollector에 통합

### 2. IPO 특화 데이터 수집
- [ ] DART API 조사 및 연동
- [ ] 공모가, 청약경쟁률 등 수집
- [ ] 기존 KRX 데이터와 병합

### 3. 실전 테스트
- [ ] 실제 KRX API 키로 테스트
- [ ] Rate Limit 모니터링
- [ ] 에러 로깅 및 복구 전략

## API 사용량 관리

### Rate Limit
- 코스닥 종목기본정보: 10,000건/일
- 코스닥 일별매매정보: 10,000건/일

### 현재 구현
- 요청 횟수 추적 (`client.request_count`)
- 90% 도달 시 경고 로그
- 100% 초과 시 에러 발생

### 최적화 방안
```python
# 전체 종목 조회 (1회 API 호출)
stocks = client.get_stock_info("20241231")

# IPO 종목만 필터링 (로컬 처리)
ipo_stocks = [s for s in stocks if s['LIST_DD'].startswith("2024")]
```

## 실제 데이터 테스트 결과

### 테스트 수행 (2025-10-07)

```bash
uv run python test_krx_api_real.py
```

**결과:**
- ✅ 2024년 12월 31일 기준 **총 1,784개** 코스닥 종목 조회 성공
- ✅ 2024년 상장 종목 **127개** 발견
- ✅ 특정 종목(교보16호스팩) 일별 매매 정보 조회 성공

**조회된 실제 데이터 예시:**
```json
{
  "ISU_NM": "교보16호스팩",
  "ISU_SRT_CD": "482520",
  "LIST_DD": "20240813",
  "TDD_OPNPRC": "2300",  // 시가
  "TDD_HGPRC": "3380",   // 고가
  "TDD_LWPRC": "2040",   // 저가
  "TDD_CLSPRC": "2060",  // 종가
  "ACC_TRDVOL": "88451222",
  "MKTCAP": "12566000000"
}
```

### 인증 방식 (중요!)

KRX API는 **Authorization Bearer 토큰** 방식을 사용합니다:
```python
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
```

❌ 잘못된 방식: `"API-KEY": api_key`
✅ 올바른 방식: `"Authorization": f"Bearer {api_key}"`

## 참고 자료

- KRX API 스펙: API 문서 (docx 파일)
- 구현 코드: `src/api/krx_client.py`, `src/data_collection/ipo_collector.py`
- 테스트: `tests/test_krx_client.py`, `test_krx_api_real.py`
- 기존 가이드: `KRX_API_INTEGRATION.md`
