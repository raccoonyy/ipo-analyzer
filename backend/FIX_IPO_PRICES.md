# IPO 가격 수정 가이드

## 현재 문제

현재 데이터셋에서 `ipo_price_confirmed`가 **액면가**(100원, 200원, 500원)로 잘못 저장되어 있습니다.
이로 인해 수익률 계산이 부정확합니다.

**예시:**
```
회사: 기가비스
현재 ipo_price_confirmed: 200원 (액면가)
실제 공모가: 약 70,000원 (추정)
day0_close: 79,000원

현재 계산: (79,000 - 200) / 200 = +39,400% (잘못됨!)
올바른 계산: (79,000 - 70,000) / 70,000 = +12.9%
```

## 해결 방법

KIS API의 공모주청약일정 API (`HHKDB669108C0`)에서 실제 공모가(`fix_subscr_pri`)를 수집합니다.

## 실행 단계

### 1단계: KIS API Rate Limit 해제 대기

현재 KIS API가 rate limit으로 403 에러를 반환하고 있습니다.
**최소 2-4시간 후**에 재시도하세요.

### 2단계: 공모가 데이터 수집

```bash
cd /Users/alan.kim/workspace/ipo-analyzer/backend

# 실제 공모가 데이터 수집 (2022-2025)
uv run python collect_ipo_prices.py
```

**예상 결과:**
```
✅ Collected 300+ IPO offering records
✅ Saved to: data/raw/ipo_offering_info.csv
```

### 3단계: 기존 데이터셋 업데이트

```bash
# 공모가로 액면가 교체
uv run python update_ipo_prices.py
```

**예상 결과:**
```
✅ Updated ipo_full_dataset_2022_2024.csv
✅ Updated ipo_full_dataset_2022_2024_enhanced.csv
✅ Updated ipo_full_dataset_2022_2024_complete.csv

Sample updates:
  기가비스 (420770):    200원 → 70,000원
  넥스트바이오메디컬: 500원 → 28,000원
```

### 4단계: 모델 재학습

```bash
# 수정된 가격으로 모델 재학습
uv run python train_model.py
```

### 5단계: 프론트엔드 예측 재생성

```bash
# 프론트엔드용 JSON 재생성 (올바른 수익률 포함)
uv run python generate_frontend_predictions.py
```

## 원스텝 실행 (권장)

모든 단계를 한 번에 실행:

```bash
cd /Users/alan.kim/workspace/ipo-analyzer/backend

# 공모가 수집 → 데이터 업데이트 → 모델 학습 → 예측 생성
uv run python collect_ipo_prices.py && \
uv run python update_ipo_prices.py && \
uv run python train_model.py && \
uv run python generate_frontend_predictions.py
```

## 에러 발생 시

### 여전히 403 에러가 발생하는 경우

더 오래 대기하거나 다음 날 시도하세요. KIS API는 일일 호출 제한이 있습니다.

### 데이터가 0개 수집되는 경우

API 응답 구조를 확인:
```bash
uv run python test_ipo_api.py
```

### 매칭되는 IPO가 적은 경우

KIS API의 종목코드와 KRX API의 종목코드가 다를 수 있습니다.
수동으로 데이터를 추가하거나 웹 스크래핑을 고려하세요.

## 예상 실행 시간

- 공모가 수집: 약 5-10분 (2022-2025, 약 400개 IPO)
- 데이터 업데이트: 1분 미만
- 모델 재학습: 약 2-5분
- 예측 생성: 1분 미만

**총 소요 시간: 약 10-20분**

## 완료 후 확인

프론트엔드 JSON 파일 확인:
```bash
cat ../frontend/public/ipo_precomputed.json | jq '.ipos[0]'
```

수익률이 합리적인 범위(-50% ~ +200%)인지 확인하세요.

---

**작성일:** 2025-10-08
**상태:** KIS API rate limit 대기 중
