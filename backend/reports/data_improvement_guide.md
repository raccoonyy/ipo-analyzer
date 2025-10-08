# 데이터 개선 가이드
**IPO 가격 예측 모델 성능 향상을 위한 추가 데이터 수집 가이드**

생성일: 2025-10-07
현재 모델 버전: v2.0

---

## 현재 상태 요약

### 보유 데이터
- ✅ 226개 완전 IPO 데이터 (2022-2024)
- ✅ 26개 features (공모 정보 + KIS API 거래 지표)
- ✅ Test R² 0.67~0.80 (실무 활용 가능)

### 주요 Feature Importance
1. **theme_encoded** (24%) - 테마/업종
2. **day1_trading_value** (27%) - 익일 거래대금
3. **day1_volume** (18%) - 익일 거래량
4. **day0_trading_value** (18%) - 상장일 거래대금

→ **거래량/거래대금 지표가 이미 핵심 역할**

---

## 추가 데이터 수집 우선순위

### 1순위: 시장 지수 데이터 ⭐⭐⭐

#### 수집 대상
- **KOSDAQ 지수**
  - 상장일 -5일 ~ +1일 (총 7일)
  - 시가, 고가, 저가, 종가, 거래량
- **KOSDAQ 거래대금**
  - 일별 시장 전체 거래대금 (유동성 지표)
- **변동성 지수**
  - VIX 또는 VKOSPI (시장 불안도)

#### 수집 방법
```python
# KRX API 사용 (이미 연동됨)
# endpoint: "kosdaq market data"

def collect_market_indices(listing_date):
    """수집 상장일 전후 시장 지수"""
    start_date = listing_date - timedelta(days=5)
    end_date = listing_date + timedelta(days=1)

    # KOSDAQ 지수 조회
    kosdaq_index = krx_client.get_kosdaq_index(start_date, end_date)

    # Feature 생성
    features = {
        "market_trend_5d": calculate_trend(kosdaq_index[-5:]),
        "market_volatility_5d": calculate_volatility(kosdaq_index[-5:]),
        "market_volume_5d_avg": kosdaq_index[-5:]["volume"].mean(),
        "market_change_day0": kosdaq_index["day0"]["change_pct"],
        "market_change_day1": kosdaq_index["day1"]["change_pct"],
    }

    return features
```

#### 예상 효과
- **Test R² 0.75 → 0.80~0.85** (5~10% 개선)
- **MAE 3,700원 → 2,800~3,200원** (15~25% 오차 감소)

#### 근거
- IPO는 시장 분위기에 매우 민감
- 시장 하락기에 상장한 IPO는 성과 저조
- 유동성 풍부한 시기에 상장하면 거래 활발

#### 난이도
- **낮음** - KRX API로 간단히 수집 가능
- 1일 소요 (100줄 이내 코드)

---

### 2순위: 경쟁 IPO 정보 ⭐⭐

#### 수집 대상
- **동일 주 상장 IPO 수**
  - 같은 주에 상장한 다른 IPO 개수
  - 청약 일정 겹치는 IPO 개수
- **동일 업종 최근 IPO 성과**
  - 최근 30일 내 동일 업종 IPO 평균 수익률
  - 최근 상장한 SPAC 평균 수익률

#### 수집 방법
```python
# 이미 수집한 데이터에서 파생 가능

def calculate_competition_features(df, current_ipo):
    """경쟁 IPO 지표 계산"""
    listing_date = current_ipo["listing_date"]

    # 동일 주 상장 IPO
    same_week = df[
        (df["listing_date"] >= listing_date - timedelta(days=3)) &
        (df["listing_date"] <= listing_date + timedelta(days=3)) &
        (df["code"] != current_ipo["code"])
    ]

    # 최근 동일 업종 IPO
    recent_same_industry = df[
        (df["listing_date"] >= listing_date - timedelta(days=30)) &
        (df["listing_date"] < listing_date) &
        (df["industry"] == current_ipo["industry"])
    ]

    features = {
        "ipo_count_same_week": len(same_week),
        "recent_industry_avg_return": recent_same_industry["day0_return"].mean(),
        "recent_industry_success_rate": (recent_same_industry["day0_return"] > 0).mean(),
    }

    return features
```

#### 예상 효과
- **Test R² 0.75 → 0.78~0.82** (3~7% 개선)
- **특히 SPAC 예측 개선 기대**

#### 근거
- IPO 과잉 공급 시 수익률 저조
- 최근 동일 업종 IPO 성공 시 투자자 관심 증가
- 청약 일정 겹치면 자금 분산

#### 난이도
- **중간** - 기존 데이터로 계산 가능
- 반나절 소요 (50줄 이내 코드)

---

### 3순위: 업종 평균 지표 ⭐

#### 수집 대상
- **업종별 평균 PER/PBR**
  - 상장일 기준 업종 평균 PER
  - 상장일 기준 업종 평균 PBR
- **업종 지수 추이**
  - 해당 업종 지수 최근 30일 변화율

#### 수집 방법
```python
# KRX 또는 금융 데이터 API 필요

def collect_industry_metrics(industry, listing_date):
    """업종 평균 지표 수집"""

    # 업종 평균 PER/PBR (한국거래소 데이터)
    industry_avg = get_industry_average(industry, listing_date)

    # 업종 지수 추이
    industry_index = get_industry_index(industry, listing_date - timedelta(days=30), listing_date)

    features = {
        "industry_avg_per": industry_avg["per"],
        "industry_avg_pbr": industry_avg["pbr"],
        "industry_trend_30d": calculate_trend(industry_index),
        "industry_volatility_30d": calculate_volatility(industry_index),
    }

    return features
```

#### 예상 효과
- **Test R² 0.75 → 0.77~0.80** (2~5% 개선)
- **업종별 예측 정확도 균등화**

#### 근거
- 고PER 업종은 IPO 프리미엄 높음
- 업종 호황기에 상장하면 높은 수익
- 현재 theme_encoded가 24% importance → 업종 정보 추가하면 더 정교한 분석 가능

#### 난이도
- **높음** - 업종별 데이터 수집 복잡
- 2~3일 소요 (외부 API 연동 필요)

---

## 보류 항목

### ❌ 일중 분봉 데이터

#### 이유
- **KIS API 제약**: 과거 분봉 데이터 조회 불가 (당일만 가능)
- **대안 부재**: 다른 무료 API도 과거 분봉 제공 안함
- **효과 불확실**: 상장일 패턴 학습 어려움 (데이터 부족)

#### 대안
- 현재 KIS API로 수집한 day0_volatility로 충분
- 추후 유료 데이터 구독 시 재검토

---

### ❌ 뉴스/SNS 데이터

#### 이유
- **수집 복잡도 매우 높음**: 크롤링, NLP 처리 필요
- **효과 불명**: 뉴스 감성 분석 정확도 낮음
- **비용 높음**: 뉴스 API 유료, 서버 리소스 많이 필요

#### 대안
- 현재 theme_encoded가 시장 관심도 어느 정도 반영
- 추후 별도 프로젝트로 분리 검토

---

### ❌ 기관/외국인 매매 데이터

#### 이유
- **데이터 공개 시차**: 상장일 익일에야 공개 (예측 불가)
- **예측 타겟과 시차 문제**: day0 예측에 사용 불가

#### 대안
- 차후 day+2, day+3 예측 모델 개발 시 활용

---

## 구현 로드맵

### Phase 1: 시장 지수 데이터 추가 (1주)
**목표:** Test R² 0.80 달성

**작업:**
1. KRX API 시장 지수 조회 함수 개발 (1일)
2. Feature engineering 업데이트 (0.5일)
3. 모델 재학습 및 평가 (0.5일)
4. 성능 비교 리포트 작성 (0.5일)

**파일 생성:**
- `collect_market_indices.py`
- `merge_market_indices.py`
- `reports/model_v3_with_market_data.md`

**예상 결과:**
- day0_high: Test R² 0.79 → 0.84
- day0_close: Test R² 0.77 → 0.82
- day1_close: Test R² 0.67 → 0.75

---

### Phase 2: 경쟁 IPO 정보 추가 (3일)
**목표:** SPAC 예측 정확도 개선

**작업:**
1. 경쟁 IPO feature 계산 함수 개발 (1일)
2. Feature engineering 업데이트 (0.5일)
3. 모델 재학습 및 평가 (0.5일)
4. SPAC 전용 분석 리포트 (1일)

**파일 생성:**
- `calculate_competition_features.py`
- `reports/spac_prediction_analysis.md`

**예상 결과:**
- SPAC 예측 MAE: 4,500원 → 3,200원
- 전체 Test R² 0.80 → 0.83

---

### Phase 3: 업종 평균 지표 추가 (1주, 선택)
**목표:** 업종별 예측 균등화

**작업:**
1. 업종 데이터 API 조사 및 연동 (2일)
2. 데이터 수집 스크립트 개발 (2일)
3. Feature engineering 업데이트 (1일)
4. 모델 재학습 및 평가 (1일)

**파일 생성:**
- `collect_industry_metrics.py`
- `merge_industry_metrics.py`

**예상 결과:**
- 업종별 예측 정확도 표준편차 감소
- Test R² 0.83 → 0.85

---

## 비용 대비 효과 분석

| 항목 | 소요 시간 | 예상 R² 개선 | 난이도 | 추천도 |
|------|----------|-------------|--------|--------|
| **시장 지수** | 1일 | +0.05~0.10 | 낮음 | ⭐⭐⭐⭐⭐ |
| **경쟁 IPO** | 0.5일 | +0.03~0.07 | 낮음 | ⭐⭐⭐⭐ |
| **업종 지표** | 2~3일 | +0.02~0.05 | 높음 | ⭐⭐ |
| 분봉 데이터 | 불가능 | 불명 | 매우 높음 | ❌ |
| 뉴스 데이터 | 1주+ | 불명 | 매우 높음 | ❌ |

---

## 코드 예시: 시장 지수 수집

```python
"""
Collect Market Indices for IPO Dates
KOSDAQ index, trading volume, volatility around IPO listing dates
"""

import pandas as pd
from datetime import timedelta
from src.api.krx_client import KRXApiClient


def collect_market_indices_for_ipos():
    """수집 IPO 상장일 전후 시장 지수"""

    # Load IPO dataset
    df_ipos = pd.read_csv("data/raw/ipo_full_dataset_2022_2024_enhanced.csv")

    # Initialize KRX client
    client = KRXApiClient()

    all_market_data = []

    for idx, row in df_ipos.iterrows():
        listing_date = pd.to_datetime(row["listing_date"])
        start_date = listing_date - timedelta(days=5)
        end_date = listing_date + timedelta(days=1)

        # Fetch KOSDAQ index
        market_data = client.get_market_index(
            "KOSDAQ",
            start_date.strftime("%Y%m%d"),
            end_date.strftime("%Y%m%d")
        )

        # Calculate features
        features = calculate_market_features(market_data, listing_date)
        features["code"] = row["code"]

        all_market_data.append(features)

    # Save
    df_market = pd.DataFrame(all_market_data)
    df_market.to_csv("data/raw/market_indices_for_ipos.csv", index=False)


def calculate_market_features(market_data, listing_date):
    """시장 지표에서 feature 계산"""

    df = pd.DataFrame(market_data)
    df["date"] = pd.to_datetime(df["date"])

    # 5-day trend before listing
    recent_5d = df[df["date"] < listing_date].tail(5)
    trend_5d = (recent_5d["close"].iloc[-1] - recent_5d["close"].iloc[0]) / recent_5d["close"].iloc[0] * 100

    # Volatility
    volatility_5d = recent_5d["close"].std() / recent_5d["close"].mean() * 100

    # Volume
    avg_volume_5d = recent_5d["volume"].mean()

    # Day 0 and Day 1 change
    day0 = df[df["date"] == listing_date].iloc[0]
    day1 = df[df["date"] == listing_date + timedelta(days=1)].iloc[0]

    return {
        "market_trend_5d": trend_5d,
        "market_volatility_5d": volatility_5d,
        "market_volume_5d_avg": avg_volume_5d,
        "market_change_day0": day0["change_pct"],
        "market_change_day1": day1["change_pct"],
    }


if __name__ == "__main__":
    collect_market_indices_for_ipos()
```

---

## 최종 권장사항

### 즉시 실행 권장
1. **시장 지수 데이터 수집** (1일 소요)
   - 가장 높은 효과 예상
   - 구현 간단
   - 무료 API 활용 가능

### 여유 시 실행
2. **경쟁 IPO 정보 추가** (반나절 소요)
   - 기존 데이터로 계산 가능
   - 추가 API 불필요

### 현재는 보류
3. **업종 평균 지표**
   - 효과 대비 작업량 높음
   - Phase 1, 2 결과 보고 결정

4. **뉴스/분봉 데이터**
   - 현실적으로 수집 어려움
   - 별도 프로젝트로 분리

---

## 현재 모델 만족도 평가

### 장점
- ✅ Test R² 0.67~0.80 (실무 활용 충분)
- ✅ 평균 오차 3,700~5,300원 (수용 가능)
- ✅ Feature importance 해석 가능
- ✅ 과적합 없음 (Train/Test 격차 적절)

### 약점
- ⚠️ 시장 전체 분위기 미반영
- ⚠️ SPAC 예측 정확도 낮음
- ⚠️ 고가 종목 오차 큼 (5~10만원대)

### 결론
**현재 모델은 실전 투자 참고용으로 충분하며, 시장 지수 데이터만 추가하면 더욱 신뢰할 수 있는 수준에 도달할 것입니다.**

**추천:** 일단 현재 모델로 실전 테스트 → 1~2개월 후 성능 평가 → 필요시 Phase 1 진행

---

**가이드 끝**
