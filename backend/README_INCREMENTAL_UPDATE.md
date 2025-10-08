# 증분 업데이트 가이드

## 개요

이제 IPO 데이터 수집 시스템이 **증분 업데이트(incremental update)**를 지원합니다.

매번 전체 데이터를 다시 수집하는 대신, **마지막 실행 이후의 신규 데이터만** 수집합니다.

---

## 핵심 개념

### 1. Last Run Tracker

**파일:** `data/.last_run.json`

```json
{
  "collect_full_data": {
    "last_run_date": "2024-12-26",
    "last_run_timestamp": "2025-10-08T00:58:25.397737"
  },
  "collect_daily_indicators": {
    "last_run_date": "2024-12-26",
    "last_run_timestamp": "2025-10-08T01:15:30.123456"
  }
}
```

이 파일은 각 데이터 수집 스크립트의 마지막 실행 날짜를 기록합니다.

### 2. 증분 수집 방식

**초기 실행:**
- `data/.last_run.json` 없음
- 전체 데이터 수집 (2022~현재)

**이후 실행:**
- 마지막 실행 날짜 이후 데이터만 수집
- 기존 데이터와 병합
- 중복 제거

---

## 사용 방법

### 방법 1: 원클릭 업데이트 (권장)

**모든 단계를 한 번에 실행:**

```bash
uv run python update_pipeline.py
```

이 명령은 다음을 순차적으로 실행합니다:
1. 신규 IPO 메타데이터 수집 (KRX API)
2. 신규 IPO 일별 지표 수집 (KIS API)
3. 지표 병합
4. 모델 재학습
5. 프론트엔드 JSON 생성

### 방법 2: 단계별 실행

**1단계: IPO 메타데이터 수집**
```bash
uv run python collect_incremental_data.py
```
- 마지막 실행 이후 신규 상장 IPO 수집
- KRX API 사용
- `ipo_full_dataset_2022_2024.csv` 업데이트

**2단계: 일별 지표 수집**
```bash
uv run python collect_daily_indicators_incremental.py
```
- 신규 IPO의 day0, day1 거래 데이터 수집
- KIS API 사용
- `ipo_daily_indicators_2022_2024.csv` 업데이트

**3단계: 지표 병합**
```bash
uv run python merge_indicators.py
```
- 거래 지표를 메타데이터와 병합
- `ipo_full_dataset_2022_2024_enhanced.csv` 생성

**4단계: 모델 재학습**
```bash
uv run python train_model.py
```
- 업데이트된 데이터로 모델 재학습
- `models/` 디렉토리 업데이트

**5단계: 프론트엔드 JSON 생성**
```bash
uv run python generate_frontend_predictions.py
```
- 전체 데이터에 대한 예측 생성
- `../frontend/public/ipo_precomputed.json` 업데이트

---

## 예시 시나리오

### 시나리오 1: 오늘 처음 설정

```bash
# 현재 상태
$ ls data/.last_run.json
파일 없음

# 첫 실행
$ uv run python collect_incremental_data.py
Collection mode: INITIAL FULL COLLECTION
Date range: 2022-01-01 to 2025-10-08
Collected 226 IPOs

# tracker 파일 생성됨
$ cat data/.last_run.json
{
  "collect_full_data": {
    "last_run_date": "2025-10-08"
  }
}
```

### 시나리오 2: 1주일 후 업데이트

```bash
# 현재: 2025-10-15
$ uv run python update_pipeline.py

# 출력:
Last collection: 2024-12-26
Collection mode: INCREMENTAL UPDATE
Date range: 2024-12-26 to 2025-10-15

COLLECTED 5 NEW IPOs
New IPOs:
  - 삼성전자신규사업(SPAC)      (500001) : 2025-10-10
  - 네이버클라우드             (500002) : 2025-10-11
  - 카카오게임즈               (500003) : 2025-10-12
  - 현대자동차수소사업부        (500004) : 2025-10-14
  - LG전자AI사업부             (500005) : 2025-10-15

Merging with existing data...
Existing records: 226
New records: 5
Total records after merge: 231

✅ All steps completed successfully!
```

### 시나리오 3: 이미 최신 상태

```bash
# 오늘 이미 실행했음
$ uv run python collect_incremental_data.py

Last collection: 2025-10-15
ALREADY UP TO DATE
Last run was on 2025-10-15, no new data to collect.
```

---

## API 사용량 절감 효과

### 기존 방식 (전체 재수집)
```
매번 실행 시:
- KRX API: 350~400 requests
- KIS API: 226 IPOs × 1 request = 226 requests
총: ~600 requests
```

### 증분 업데이트 방식
```
신규 IPO 5개만 수집 시:
- KRX API: 5~10 requests
- KIS API: 5 requests
총: ~15 requests (97% 절감!)
```

---

## 파일 구조

```
backend/
├── data/
│   ├── .last_run.json                        # 마지막 실행 기록 (새로 생성)
│   └── raw/
│       ├── ipo_full_dataset_2022_2024.csv    # 증분 업데이트됨
│       ├── ipo_full_dataset_2022_2024_enhanced.csv
│       └── daily_indicators/
│           └── ipo_daily_indicators_2022_2024.csv
│
├── src/
│   └── utils/
│       └── last_run_tracker.py               # Tracker 클래스 (새로 생성)
│
├── collect_incremental_data.py               # 증분 수집 스크립트 (새로 생성)
├── collect_daily_indicators_incremental.py   # 증분 수집 (새로 생성)
├── update_pipeline.py                        # 원클릭 업데이트 (새로 생성)
│
├── collect_full_data.py                      # 기존 (여전히 사용 가능)
├── collect_daily_indicators.py               # 기존 (여전히 사용 가능)
├── merge_indicators.py
├── train_model.py
└── generate_frontend_predictions.py
```

---

## 주의사항

### 1. `.last_run.json` 삭제 시

**주의:** 이 파일을 삭제하면 다음 실행 시 **전체 데이터를 다시 수집**합니다.

```bash
# 전체 재수집이 필요한 경우
$ rm data/.last_run.json
$ uv run python update_pipeline.py
```

### 2. 수동으로 날짜 조정

```bash
# 특정 날짜부터 재수집하고 싶은 경우
$ uv run python -c "
from src.utils.last_run_tracker import LastRunTracker
from datetime import date

tracker = LastRunTracker()
tracker.update_last_run('collect_full_data', date(2024, 10, 1))
print('✅ Last run set to 2024-10-01')
"

$ uv run python collect_incremental_data.py
# 2024-10-01 이후 데이터만 수집됨
```

### 3. 전체 재수집 vs 증분 수집

**전체 재수집 (기존 방식):**
```bash
uv run python collect_full_data.py
uv run python collect_daily_indicators.py
```
- 모든 데이터 재수집
- 시간 많이 소요 (~10분)
- API 사용량 높음

**증분 수집 (새 방식):**
```bash
uv run python update_pipeline.py
```
- 신규 데이터만 수집
- 빠름 (~1분)
- API 사용량 낮음

---

## 자동화 예시

### Cron Job (매일 자동 업데이트)

```bash
# crontab -e

# 매일 오전 9시에 IPO 데이터 업데이트
0 9 * * * cd /path/to/ipo-analyzer/backend && uv run python update_pipeline.py >> logs/update.log 2>&1
```

### GitHub Actions (주간 자동 업데이트)

```yaml
name: Update IPO Data

on:
  schedule:
    - cron: '0 0 * * 0'  # 매주 일요일 자동 실행
  workflow_dispatch:      # 수동 실행 가능

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install uv
        run: pip install uv

      - name: Run update pipeline
        env:
          KRX_API_KEY: ${{ secrets.KRX_API_KEY }}
          KIS_APP_KEY: ${{ secrets.KIS_APP_KEY }}
          KIS_APP_SECRET: ${{ secrets.KIS_APP_SECRET }}
        run: |
          cd backend
          uv run python update_pipeline.py

      - name: Commit updated data
        run: |
          git config --local user.name "GitHub Action"
          git config --local user.email "action@github.com"
          git add data/ frontend/public/ipo_precomputed.json
          git commit -m "chore: update IPO data [skip ci]" || true
          git push
```

---

## 트러블슈팅

### 문제 1: "Already up to date"인데 데이터가 누락됨

**원인:** Tracker 날짜가 잘못 설정됨

**해결:**
```bash
# Tracker 초기화
rm data/.last_run.json

# 전체 재수집
uv run python collect_full_data.py
```

### 문제 2: 중복 데이터 발생

**원인:** 병합 로직 오류

**해결:**
```bash
# 기존 파일 백업
cp data/raw/ipo_full_dataset_2022_2024.csv data/raw/backup.csv

# 전체 재수집
rm data/.last_run.json
uv run python collect_full_data.py
```

### 문제 3: API 인증 실패

**원인:** 토큰 만료 또는 credential 오류

**해결:**
```bash
# .env 파일 확인
cat .env | grep KIS_APP_KEY

# 재인증 테스트
uv run python -c "
from src.api.kis_client import KISApiClient
client = KISApiClient()
client.authenticate()
print('✅ Authentication successful')
"
```

---

## FAQ

**Q: 증분 업데이트 사용 시 모델 성능이 떨어질까요?**

A: 아니요. 모델은 매번 전체 데이터로 재학습하므로 성능은 동일합니다. 증분 수집은 **데이터 수집만** 최적화한 것입니다.

**Q: 얼마나 자주 업데이트해야 하나요?**

A:
- **실시간 서비스:** 매일 1회 (오전 9시 권장)
- **개인 분석:** 주 1회 (주말 권장)
- **백테스팅 연구:** 월 1회

**Q: 전체 재수집은 언제 필요한가요?**

A:
- 데이터 오류가 발견된 경우
- API 스키마 변경된 경우
- 3개월 이상 업데이트 안 한 경우

**Q: `.last_run.json`을 git에 커밋해야 하나요?**

A: 아니요. 이 파일은 로컬 실행 기록이므로 `.gitignore`에 추가하세요.

```bash
echo "data/.last_run.json" >> .gitignore
```

---

## 마이그레이션 가이드

### 기존 시스템에서 증분 업데이트로 전환

**1단계: Tracker 초기화**
```bash
# 현재 데이터의 마지막 날짜로 초기화
uv run python -c "
from src.utils.last_run_tracker import LastRunTracker
from datetime import date

tracker = LastRunTracker()
tracker.update_last_run('collect_full_data', date(2024, 12, 26))
tracker.update_last_run('collect_daily_indicators', date(2024, 12, 26))
print('✅ Tracker initialized')
"
```

**2단계: 증분 업데이트 테스트**
```bash
uv run python collect_incremental_data.py
```

**3단계: 전체 파이프라인 테스트**
```bash
uv run python update_pipeline.py
```

---

**완성!** 이제 증분 업데이트 시스템을 사용할 수 있습니다. 🎉
