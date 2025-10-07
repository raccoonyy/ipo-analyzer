# TODO - Task Tracking

## Completed Tasks

### ✅ Project Setup
- [x] Create project directory structure
  - `src/` modules: data_collection, features, models, prediction
  - `data/` directories: raw, processed
  - `models/`, `output/`, `config/` directories
- [x] Configure uv package manager
  - Setup `pyproject.toml` with dependencies
  - Configure `[tool.hatch.build.targets.wheel]` for src layout
  - Add dev dependencies to `[tool.uv]` section
  - Run `uv sync` to install 119 packages
- [x] Create `.gitignore` for Python, uv, and project-specific files
- [x] Create `__init__.py` files for all modules

### ✅ Data Collection Module
- [x] Implement `IPODataCollector` class (`src/data_collection/ipo_collector.py`)
  - `collect_ipo_metadata()` - Collect IPO metadata for specified year range
  - `collect_intraday_prices()` - Fetch intraday execution price data
  - `get_highest_and_closing_price()` - Extract highest and closing prices
  - `collect_full_dataset()` - Combine metadata with Day 0 and Day 1 prices
- [x] Define all required IPO metadata fields:
  - Price band (lower, upper, confirmed)
  - Shares offered, institutional demand rate
  - Lock-up ratio, subscription competition rate
  - Paid-in capital, estimated market cap
  - Listing method, allocation ratios
  - Industry, theme

### ✅ Feature Engineering Module
- [x] Implement `IPOFeatureEngineer` class (`src/features/feature_engineering.py`)
  - `engineer_features()` - Transform raw data to ML-ready features
  - `prepare_training_data()` - Prepare X, y, metadata for training
  - `save_transformers()` - Persist fitted scalers and encoders
  - `load_transformers()` - Load pre-fitted transformers
- [x] Create engineered features:
  - Price-related: range, range_pct, positioning
  - Financial: market_cap_ratio, total_offering_value
  - Demand: demand_to_lockup_ratio, high_competition, high_demand
  - Temporal: month, quarter, day_of_week
  - Allocation: allocation_balance
- [x] Implement categorical encoding (LabelEncoder)
- [x] Implement feature scaling (StandardScaler)
- [x] Handle unseen categories gracefully

### ✅ Model Training Module
- [x] Implement `IPOPricePredictor` class (`src/models/ipo_predictor.py`)
  - Support Random Forest and Gradient Boosting models
  - Train separate models for each target (day0_high, day0_close, day1_close)
  - `train()` - Train all models with train/test split
  - `predict()` - Generate predictions for new data
  - `save_models()` - Persist trained models to disk
  - `load_models()` - Load pre-trained models
  - `get_feature_importance()` - Analyze feature importance
- [x] Implement comprehensive evaluation metrics:
  - MAE (Mean Absolute Error)
  - RMSE (Root Mean Squared Error)
  - R² (Coefficient of Determination)
  - MAPE (Mean Absolute Percentage Error)
- [x] Save evaluation metrics to JSON

### ✅ Prediction Generation Module
- [x] Implement `PredictionGenerator` class (`src/prediction/generate_predictions.py`)
  - `generate_predictions_for_dataset()` - Generate predictions for IPO dataset
  - `generate_and_save()` - Full pipeline to create JSON output
  - `_print_summary()` - Display prediction statistics
  - `_calculate_accuracy()` - Calculate prediction accuracy if actuals available
- [x] Format predictions to JSON structure matching specification
- [x] Include metadata in output (shares, demand rates, industry, theme)
- [x] Round predictions to integer KRW values
- [x] Handle model loading and automatic training fallback

### ✅ Configuration
- [x] Create `config/config.yaml` with all settings:
  - Data collection parameters (year range, API endpoints)
  - Feature engineering settings (features, thresholds)
  - Model training settings (type, hyperparameters, split ratio)
  - Prediction output settings (file path, formatting)
  - Logging configuration

### ✅ Dependencies Management
- [x] Add core dependencies to `pyproject.toml`:
  - pandas >= 2.0.0
  - numpy >= 1.24.0
  - scikit-learn >= 1.3.0
  - requests >= 2.31.0
- [x] Add dev dependencies:
  - pytest >= 7.4.0
  - jupyter >= 1.0.0
  - matplotlib >= 3.7.0
  - seaborn >= 0.12.0

### ✅ Documentation
- [x] Create `README.md` with:
  - Project overview
  - Installation instructions
  - All command usage
  - Project structure
  - Configuration guide
  - Development workflow
  - Output format specification
- [x] Create `SPEC.md` with detailed requirements:
  - Context and objectives
  - Data collection specifications
  - Prediction targets
  - JSON output structure
  - Data processing pipeline
  - Technology stack
  - Model evaluation metrics
  - Configuration parameters
  - Future enhancements
- [x] Create `TODO.md` (this file)

## Pending Tasks

### 🔲 KRX API Integration
- [ ] Research KRX API documentation
- [ ] Obtain API credentials/access
- [ ] Implement `collect_ipo_metadata()` with real API calls
  - Location: `src/data_collection/ipo_collector.py:24`
  - Replace placeholder data with actual KRX IPO metadata endpoint
- [ ] Implement `collect_intraday_prices()` with real API calls
  - Location: `src/data_collection/ipo_collector.py:62`
  - Replace placeholder data with actual KRX market data endpoint
- [ ] Add error handling for API failures (timeout, rate limits, errors)
- [ ] Add retry logic with exponential backoff
- [ ] Update `config/config.yaml` with actual API endpoints

### ✅ Testing
- [x] Write unit tests for `IPODataCollector`
- [x] Write unit tests for `IPOFeatureEngineer`
- [x] Write unit tests for `IPOPricePredictor`
- [x] Write unit tests for `PredictionGenerator`
- [ ] Write integration tests for full pipeline
- [x] Add test fixtures with sample IPO data
- [x] Configure pytest settings
- [x] Add black formatter for code formatting
- [x] Achieve 81% code coverage (24 tests passing)

### 🔲 Model Improvements
- [ ] Implement hyperparameter tuning (GridSearchCV / RandomizedSearchCV)
- [ ] Add cross-validation for more robust evaluation
- [ ] Experiment with additional model types (XGBoost, LightGBM)
- [ ] Implement ensemble methods (stacking, voting)
- [ ] Add feature selection techniques
- [ ] Implement time-series cross-validation
- [ ] Add prediction confidence intervals

### ✅ Data Validation
- [x] Add input data validation (check for missing values, outliers)
- [x] Implement data quality checks (DataValidator module)
- [x] Add logging throughout the pipeline (logger in all modules)
- [x] Create logging configuration utility
- [x] Add 11 tests for DataValidator
- [ ] Create data profiling reports
- [ ] Handle edge cases (IPOs with unusual characteristics)

### 🔲 Deployment
- [ ] Create Docker container for backend
- [ ] Add CI/CD pipeline configuration
- [ ] Create model retraining schedule
- [ ] Add model versioning system
- [ ] Create API endpoint for real-time predictions (future enhancement)
- [ ] Add monitoring and alerting

### 🔲 Additional Features
- [ ] Add visualization module (feature importance plots, prediction distributions)
- [ ] Create Jupyter notebooks for exploratory data analysis
- [ ] Add CLI interface with argparse
- [ ] Implement incremental learning for new IPO data
- [ ] Add support for multiple market exchanges (beyond KRX)

## Notes

### Technical Debt
- Current implementation uses placeholder data for KRX API calls
- Limited error handling in prediction generation

### Known Issues
- None currently

### Dependencies
- KRX API integration is a blocker for production use
- All other modules are functional with placeholder data for development/testing

### Timeline
- Phase 1 (Completed): Core architecture and modules
- Phase 2 (In Progress): KRX API integration
- Phase 3 (Planned): Testing and validation
- Phase 4 (Planned): Model improvements and optimization
- Phase 5 (Planned): Deployment and monitoring
