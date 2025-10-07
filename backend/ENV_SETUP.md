# Environment Variables Setup

## Overview

이 프로젝트는 환경변수를 통해 설정을 관리합니다. `.env` 파일을 사용하여 로컬 개발 환경을 구성할 수 있습니다.

## Quick Start

1. **`.env` 파일 생성**
   ```bash
   cp .env.example .env
   ```

2. **필요한 값 설정**
   ```bash
   # .env 파일을 열어 실제 값으로 수정
   vim .env
   ```

3. **애플리케이션 실행**
   ```bash
   uv run python src/data_collection/ipo_collector.py
   ```

## Environment Variables

### 필수 환경변수 (프로덕션)

프로덕션 환경에서는 다음 변수들이 **필수**입니다:

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `KRX_API_KEY` | KRX API 인증 키 | `your_api_key_here` |
| `KRX_API_SECRET` | KRX API 시크릿 키 | `your_api_secret_here` |
| `ENVIRONMENT` | 실행 환경 | `production` |

### 선택적 환경변수

다음 변수들은 기본값이 있어 선택적입니다:

#### KRX API 설정
- `KRX_API_BASE_URL` (기본값: `https://api.krx.co.kr`)
- `KRX_API_TIMEOUT` (기본값: `30`)
- `KRX_API_RETRY_ATTEMPTS` (기본값: `3`)

#### 애플리케이션 설정
- `ENVIRONMENT` (기본값: `development`)
- `LOG_LEVEL` (기본값: `INFO`)
- `LOG_FILE` (기본값: `logs/ipo_analyzer.log`)

#### 데이터 설정
- `DATA_START_YEAR` (기본값: `2022`)
- `DATA_END_YEAR` (기본값: `2025`)
- `DATA_RAW_DIR` (기본값: `data/raw`)
- `DATA_PROCESSED_DIR` (기본값: `data/processed`)
- `MODELS_DIR` (기본값: `models`)
- `OUTPUT_DIR` (기본값: `output`)

#### 모델 설정
- `MODEL_TYPE` (기본값: `random_forest`)
- `RF_N_ESTIMATORS` (기본값: `100`)
- `RF_MAX_DEPTH` (기본값: `15`)
- `RF_MIN_SAMPLES_SPLIT` (기본값: `5`)
- `RF_MIN_SAMPLES_LEAF` (기본값: `2`)
- `MODEL_TEST_SIZE` (기본값: `0.2`)
- `MODEL_RANDOM_STATE` (기본값: `42`)

## 사용 예시

### 개발 환경 (.env)
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DATA_START_YEAR=2023
DATA_END_YEAR=2024
```

### 프로덕션 환경 (.env)
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
KRX_API_KEY=actual_api_key_here
KRX_API_SECRET=actual_secret_here
KRX_API_BASE_URL=https://actual-api.krx.co.kr
```

## 코드에서 사용하기

```python
from src.config import settings

# 환경변수 값 읽기
api_key = settings.KRX_API_KEY
log_level = settings.LOG_LEVEL
start_year = settings.DATA_START_YEAR

# 환경 체크
if settings.is_production():
    # 프로덕션 전용 로직
    settings.validate()  # 필수 변수 검증
```

## 주의사항

⚠️ **보안 주의사항**
- `.env` 파일은 **절대 git에 커밋하지 마세요**
- `.env` 파일에는 민감한 정보(API 키, 시크릿 등)가 포함됩니다
- `.gitignore`에 `.env` 파일이 포함되어 있는지 확인하세요

✅ **올바른 방법**
- `.env.example` 파일을 템플릿으로 사용
- 각 환경(개발/스테이징/프로덕션)마다 별도의 `.env` 파일 관리
- CI/CD 파이프라인에서는 환경변수를 직접 주입

## 검증

환경변수가 올바르게 설정되었는지 확인:

```bash
uv run python -c "from src.config import settings; print(f'Environment: {settings.ENVIRONMENT}'); print(f'Log Level: {settings.LOG_LEVEL}')"
```

프로덕션 환경 검증:

```python
from src.config import settings

try:
    settings.validate()
    print("✓ All required environment variables are set")
except ValueError as e:
    print(f"✗ Missing required environment variable: {e}")
```

## 트러블슈팅

### 문제: `.env` 파일이 로드되지 않음
**해결**: `.env` 파일이 프로젝트 루트 디렉토리(`backend/`)에 있는지 확인

### 문제: 환경변수 값이 반영되지 않음
**해결**: 애플리케이션을 재시작하거나, 캐시된 imports를 제거

### 문제: 프로덕션 환경에서 오류 발생
**해결**: `settings.validate()`를 실행하여 필수 변수가 모두 설정되었는지 확인
