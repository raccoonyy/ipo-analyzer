# IPO Analyzer - Requirements Specification

## Context

Building a web service that predicts the highest execution price on the IPO day, the closing price on the IPO day, and the closing price on the following day for newly listed stocks based on IPO-related features.

All predictions should be **precomputed on the backend** and stored in a static JSON file for the frontend to directly consume without real-time calculations.

## Requirements

### 1. Data Collection

Collect IPO metadata for companies listed between 2022 and 2025:

#### IPO Metadata Features
- **IPO price band**
  - Lower bound price
  - Upper bound price
  - Confirmed IPO price
- **Number of shares offered** - Total shares available in IPO
- **Institutional demand forecast rate** - Pre-IPO institutional investor demand (%)
- **Lock-up ratio** - Percentage of shares with mandatory holding period (%)
- **Public subscription competition rate** - Oversubscription ratio (e.g., 1234:1)
- **Paid-in capital** - Total paid-in capital (KRW)
- **Estimated market cap** - Expected market capitalization at IPO price (KRW)
- **Listing method** - Type of listing (e.g., General, Book-building)
- **Equal vs proportional allocation ratio**
  - Equal allocation percentage (%)
  - Proportional allocation percentage (%)
- **Industry** - Business sector classification
- **Theme** - Investment theme/category

#### Intraday Price Data
- **IPO day (Day 0)** execution prices
  - Intraday tick-by-tick or minute-by-minute price data
  - Extract: highest execution price, closing price
- **Next day (Day 1)** execution prices
  - Intraday tick-by-tick or minute-by-minute price data
  - Extract: highest execution price, closing price

### 2. Prediction Targets

Train machine learning models to predict:

1. **Day 0 highest execution price** - Peak price reached on IPO day
2. **Day 0 closing price** - Closing price on IPO day
3. **Day 1 closing price** - Closing price on the following trading day

### 3. Static JSON Output

Generate a precomputed predictions file for frontend consumption.

#### File Path
`output/ipo_precomputed.json`

#### JSON Structure
```json
[
  {
    "company_name": "ExampleTech",
    "code": "123456",
    "listing_date": "2024-10-01",
    "ipo_price": 22000,
    "predicted": {
      "day0_high": 24000,
      "day0_close": 22000,
      "day1_close": 21000
    },
    "metadata": {
      "shares_offered": 1000000,
      "institutional_demand_rate": 850.5,
      "subscription_competition_rate": 1234.56,
      "industry": "IT",
      "theme": "TECH"
    }
  }
]
```

#### Field Descriptions
- `company_name` - Company name (string)
- `code` - Stock code (string)
- `listing_date` - IPO listing date (YYYY-MM-DD)
- `ipo_price` - Confirmed IPO price (integer, KRW)
- `predicted` - ML model predictions (object)
  - `day0_high` - Predicted highest price on IPO day (integer, KRW)
  - `day0_close` - Predicted closing price on IPO day (integer, KRW)
  - `day1_close` - Predicted closing price on next day (integer, KRW)
- `metadata` - Additional IPO information (object)
  - `shares_offered` - Number of shares (integer)
  - `institutional_demand_rate` - Demand rate (float, %)
  - `subscription_competition_rate` - Competition ratio (float)
  - `industry` - Industry classification (string)
  - `theme` - Investment theme (string)

### 4. Data Processing Pipeline

#### Stage 1: Data Collection
- Collect IPO metadata from KRX (Korea Exchange)
- Collect intraday execution price data for Day 0 and Day 1
- Store raw data in `data/raw/`

#### Stage 2: Feature Engineering
- Transform raw metadata into ML-ready features
- Create derived features:
  - Price range percentage
  - Price positioning within band
  - Market cap ratio
  - Demand to lock-up ratio
  - Temporal features (month, quarter, weekday)
  - Binary indicators (high competition, high demand)
- Encode categorical variables (listing method, industry, theme)
- Scale numerical features using StandardScaler
- Store transformers in `data/processed/`

#### Stage 3: Model Training
- Train separate models for each target variable
- Default algorithm: Random Forest Regressor
- Alternative: Gradient Boosting Regressor
- Split: 80% train, 20% test
- Evaluate using: MAE, RMSE, R², MAPE
- Store trained models in `models/`

#### Stage 4: Prediction Generation
- Load trained models and transformers
- Generate predictions for all IPOs (2022-2025)
- Round predictions to nearest integer (KRW)
- Output to `output/ipo_precomputed.json`

### 5. Technology Stack

- **Language**: Python 3.13+
- **Package Manager**: uv
- **ML Framework**: scikit-learn
- **Data Processing**: pandas, numpy
- **HTTP Requests**: requests (for KRX API)
- **Configuration**: YAML

### 6. Data Sources

**KRX (Korea Exchange) API**
- IPO metadata endpoint
- Intraday market data endpoint

**Note**: API integration to be implemented. Current code uses placeholder data.

### 7. Model Evaluation Metrics

- **MAE (Mean Absolute Error)** - Average prediction error in KRW
- **RMSE (Root Mean Squared Error)** - Penalizes larger errors
- **R² (Coefficient of Determination)** - Variance explained (0-1)
- **MAPE (Mean Absolute Percentage Error)** - Percentage error

### 8. Configuration Parameters

Defined in `config/config.yaml`:

- **Data Collection**
  - Year range: 2022-2025
  - API endpoints
  - Timeout and retry settings

- **Feature Engineering**
  - Feature selection
  - Threshold values for binary features

- **Model Training**
  - Model type (Random Forest / Gradient Boosting)
  - Hyperparameters (n_estimators, max_depth, etc.)
  - Train/test split ratio

- **Prediction Output**
  - Output file path
  - Rounding options
  - Metadata inclusion settings

### 9. Non-Functional Requirements

- **Performance**: Precompute all predictions (no real-time ML inference)
- **Scalability**: Handle 100+ IPOs across 4 years
- **Maintainability**: Modular architecture with clear separation of concerns
- **Reproducibility**: Fixed random seeds, version-controlled dependencies
- **Data Format**: UTF-8 encoding for Korean text support

### 10. Future Enhancements

- Real-time prediction API endpoint
- Additional features (macroeconomic indicators, market sentiment)
- Ensemble models (combine multiple algorithms)
- Hyperparameter tuning (GridSearchCV, RandomizedSearchCV)
- Time-series cross-validation
- Model retraining pipeline
- Prediction confidence intervals
- A/B testing framework for model versions
