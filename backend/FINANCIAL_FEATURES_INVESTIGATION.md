# Financial Features Investigation Summary

## Overview

Investigated adding financial metrics (PER, PBR, EPS) to improve IPO return prediction model accuracy.

## Key Findings

### 1. KIS API Limitations

**Discovery**: KIS API does NOT provide PER/PBR/EPS in historical daily OHLCV data
- `get_daily_ohlcv()` endpoint: Returns OHLCV but NO financial metrics
- `get_current_price()` endpoint: Has PER/PBR but ONLY for current time
- Result: All financial feature values were 0.0 in dataset (452 records)

**Test Results**:
- Samsung (005930): PER=17.98, PBR=1.54 ✅
- IPO stocks: PER=0.00, PBR=0.00 ❌

### 2. 38.co.kr as Alternative Source

**URL Format**: `https://www.38.co.kr/html/fund/?o=v&no={fund_no}`

**Available Data** (Example: 명인제약, no=2220):
- Historical PER by year: 2022=11.45, 2023=8.89, 2024=9.82
- Historical PBR by year: 2022=1.55, 2023=1.39, 2024=1.24
- Historical EPS by year: 2022=5,067, 2023=6,523, 2024=6,131
- ROE, BPS, Revenue, Net Income also available

**Challenges**:
1. **Mapping Problem**: Need stock_code → fund_no mapping
   - Newly listed page (`o=nw`) only has ~10 recent (2025) IPOs
   - Our dataset has 155 IPOs from 2022-2024
   - No easy way to access historical mappings programmatically

2. **Systematic Collection**: Would require:
   - Manual mapping creation, OR
   - Brute force search through fund_no values, OR
   - Alternative pagination/search approach

### 3. Model Performance Analysis

#### Original Model (226 IPOs with SPAC):
```
day0_close: R² = 0.773, MAPE = 37.8%
day0_high:  R² = 0.809, MAPE = 37.3%
day1_close: R² = 0.773, MAPE = N/A
```

#### After SPAC Exclusion + Zero-Value Financial Features (155 IPOs):
```
day0_close: R² = 0.51, MAPE = 44.1%  ❌ -26% worse
```

**Root Causes**:
1. **Sample Size Reduction**: 226 → 155 IPOs (-31%) due to SPAC exclusion
2. **Noise from Zero Features**: Added 4 financial features with all 0 values
3. **Feature Importance**: Financial features contributed 0.0 (unused by model)

## Actions Taken

1. ✅ Created `collect_38_financial_metrics.py` - Scraper for 38.co.kr financial data
2. ✅ Modified `merge_indicators.py` to include PER/PBR/EPS columns
3. ✅ Updated `feature_engineering.py` with financial features
4. ✅ Restored backup models (original performance maintained)
5. ✅ Documented findings in this file

## Recommendations

### Short-term (Current Status)
**DONE**: Restored original models with R² = 0.773

### Medium-term Options

#### Option A: Keep SPAC, Remove Zero-Value Features
- Revert SPAC exclusion (restore 226 IPOs)
- Remove zero-value financial feature columns
- Retrain model to validate performance

#### Option B: Manual Financial Data Collection
- Manually create stock_code → fund_no mapping for subset of IPOs
- Use `collect_38_financial_metrics.py` to fetch real financial data
- Merge into dataset and retrain
- Time investment: ~2-3 hours for 50-100 companies

#### Option C: Alternative Data Sources
- DART (전자공시시스템): Official financial statements
- KRX API: May have financial ratios
- Naver Finance / Daum Finance: Stock financial data APIs

### Long-term
- Implement proper financial data pipeline using official sources (DART)
- Create automated mapping system for 38.co.kr
- Evaluate if financial features significantly improve predictions (ROI analysis)

## Files Created/Modified

**New Files**:
- `collect_38_financial_metrics.py` - 38.co.kr scraper
- `data/raw/38_financial_metrics.csv` - Empty results (no mappings found)
- `models_backup_before_financial/` - Original model backup

**Modified Files**:
- `merge_indicators.py` - Added PER/PBR/EPS column mappings (lines 46-51, 63-68)
- `src/features/feature_engineering.py` - Added financial features (lines 119-124)
- `data/raw/ipo_full_dataset_2022_2024_enhanced.csv` - SPAC filtered, 155 IPOs

**Restored Files**:
- `models/*.pkl` - Restored from backup (R² = 0.773)

## Final Results

### ✅ Data Collection Success

Successfully collected financial metrics from 38.co.kr:
- **Found mapping**: `38_subscription_data.csv` contains `ipo_no` for 358 IPOs
- **Coverage**: 62/155 IPOs (40%) have financial data (PER/PBR/EPS)
- **Data quality**: Real historical financial metrics, not zeros

### ❌ Model Performance Did Not Improve

**Baseline** (226 IPOs, no financial features):
- day0_close: R² = 0.773, MAPE = 37.8%

**With Financial Features** (155 IPOs, 3 new features):
- day0_close: R² = 0.499, MAPE = 45.2%

**Performance declined by 27%**

### Root Causes

1. **Sample Size Reduction**: SPAC exclusion reduced training data by 31% (226 → 155)
2. **Missing Data**: 60% of IPOs have no financial metrics → model can't rely on these features
3. **Feature Importance**: `listing_per/pbr/eps` didn't appear in Top 10 features
4. **Missing Value Handling**: scikit-learn's imputation strategy may not work well with 60% missing rate

### Files Created

**Successful Deliverables:**
- `collect_38_financial_metrics.py` - Working scraper using `ipo_no` mapping
- `data/raw/38_financial_metrics.csv` - 62 IPOs with PER/PBR/EPS
- `data/raw/ipo_full_dataset_2022_2024_with_financials.csv` - Merged dataset
- `merge_38_financial_data.py` - Merging script

**Model Status:**
- ✅ Original models restored (R² = 0.773)
- ❌ Financial feature models discarded (R² = 0.499)

## Conclusion

Financial metrics (PER/PBR/EPS) ARE available from 38.co.kr with historical values and were successfully collected for 40% of IPOs. However, adding these features **decreased** model performance due to:
1. Reduced sample size from SPAC exclusion
2. High missing data rate (60%)
3. Model's inability to utilize sparse features effectively

**Recommendation**: Keep current model (R² = 0.773) without financial features. Financial features could be valuable in the future if:
- More comprehensive data source is found (>80% coverage)
- Sample size is maintained (don't exclude SPAC)
- Advanced imputation techniques are used
- Separate model is built specifically for IPOs with financial data
