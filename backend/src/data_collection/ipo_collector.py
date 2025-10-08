"""
IPO Data Collection Module
Collects IPO metadata and execution price data from KRX for 2022-2025
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import requests
from pathlib import Path
import logging
from tqdm import tqdm
from src.api.krx_client import KRXApiClient
from src.config.settings import settings
from src.data_collection.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class IPODataCollector:
    """Collects IPO metadata and intraday price data"""

    def __init__(self, data_dir: str = "data/raw", use_sample_data: bool = False):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.use_sample_data = use_sample_data
        self.cache_manager = CacheManager()

        # Initialize KRX API client if not using sample data
        if not use_sample_data:
            if not settings.KRX_API_KEY:
                logger.warning(
                    "KRX_API_KEY not found in environment. Falling back to sample data."
                )
                self.use_sample_data = True
            else:
                self.krx_client = KRXApiClient(
                    api_key=settings.KRX_API_KEY,
                    timeout=settings.KRX_API_TIMEOUT,
                    use_cache=True,
                )
                logger.info("Initialized KRXApiClient with cache enabled")

        logger.info(
            f"Initialized IPODataCollector with data_dir: {self.data_dir}, "
            f"use_sample_data: {self.use_sample_data}"
        )

    def collect_ipo_metadata(
        self, start_year: int = 2022, end_year: int = 2025, optimized: bool = True
    ) -> pd.DataFrame:
        """
        Collect IPO metadata for companies listed between start_year and end_year

        Features collected:
        - IPO price band (lower, upper, confirmed)
        - Number of shares offered
        - Institutional demand forecast rate
        - Lock-up ratio
        - Public subscription competition rate
        - Paid-in capital / Estimated market cap
        - Listing method
        - Equal vs proportional allocation ratio
        - Industry / theme

        Args:
            start_year: Start year for data collection
            end_year: End year for data collection
            optimized: Use optimized collection (1 API call vs 48) - default True
        """
        if self.use_sample_data:
            return self._collect_sample_metadata(start_year, end_year)

        # Use optimized or legacy method
        if optimized:
            return self._collect_krx_metadata_optimized(start_year, end_year)
        else:
            return self._collect_krx_metadata(start_year, end_year)

    def _collect_sample_metadata(self, start_year: int, end_year: int) -> pd.DataFrame:
        """Generate sample data for testing"""
        metadata = []

        sample_companies = [
            {
                "company_name": "TechCorp A",
                "code": "100001",
                "listing_date": "2024-01-15",
                "ipo_price_lower": 18000,
                "ipo_price_upper": 22000,
                "ipo_price_confirmed": 20000,
                "shares_offered": 1000000,
                "institutional_demand_rate": 500.0,
                "lockup_ratio": 25.0,
                "subscription_competition_rate": 800.0,
                "paid_in_capital": 40000000000,
                "estimated_market_cap": 200000000000,
                "listing_method": "GENERAL",
                "allocation_ratio_equal": 40.0,
                "allocation_ratio_proportional": 60.0,
                "industry": "IT",
                "theme": "TECH",
            },
            {
                "company_name": "BioPharma B",
                "code": "100002",
                "listing_date": "2024-02-20",
                "ipo_price_lower": 25000,
                "ipo_price_upper": 30000,
                "ipo_price_confirmed": 28000,
                "shares_offered": 500000,
                "institutional_demand_rate": 1200.0,
                "lockup_ratio": 30.0,
                "subscription_competition_rate": 1500.0,
                "paid_in_capital": 50000000000,
                "estimated_market_cap": 280000000000,
                "listing_method": "BOOK_BUILDING",
                "allocation_ratio_equal": 50.0,
                "allocation_ratio_proportional": 50.0,
                "industry": "BIOTECH",
                "theme": "HEALTHCARE",
            },
            {
                "company_name": "GreenEnergy C",
                "code": "100003",
                "listing_date": "2024-03-10",
                "ipo_price_lower": 15000,
                "ipo_price_upper": 18000,
                "ipo_price_confirmed": 17000,
                "shares_offered": 800000,
                "institutional_demand_rate": 600.0,
                "lockup_ratio": 20.0,
                "subscription_competition_rate": 950.0,
                "paid_in_capital": 35000000000,
                "estimated_market_cap": 170000000000,
                "listing_method": "GENERAL",
                "allocation_ratio_equal": 45.0,
                "allocation_ratio_proportional": 55.0,
                "industry": "ENERGY",
                "theme": "GREEN",
            },
            {
                "company_name": "FinTech D",
                "code": "100004",
                "listing_date": "2024-04-25",
                "ipo_price_lower": 30000,
                "ipo_price_upper": 35000,
                "ipo_price_confirmed": 33000,
                "shares_offered": 600000,
                "institutional_demand_rate": 1500.0,
                "lockup_ratio": 35.0,
                "subscription_competition_rate": 2000.0,
                "paid_in_capital": 60000000000,
                "estimated_market_cap": 330000000000,
                "listing_method": "BOOK_BUILDING",
                "allocation_ratio_equal": 50.0,
                "allocation_ratio_proportional": 50.0,
                "industry": "FINANCE",
                "theme": "FINTECH",
            },
            {
                "company_name": "AIRobotics E",
                "code": "100005",
                "listing_date": "2024-05-30",
                "ipo_price_lower": 22000,
                "ipo_price_upper": 26000,
                "ipo_price_confirmed": 24000,
                "shares_offered": 700000,
                "institutional_demand_rate": 900.0,
                "lockup_ratio": 28.0,
                "subscription_competition_rate": 1300.0,
                "paid_in_capital": 45000000000,
                "estimated_market_cap": 240000000000,
                "listing_method": "GENERAL",
                "allocation_ratio_equal": 42.0,
                "allocation_ratio_proportional": 58.0,
                "industry": "IT",
                "theme": "AI",
            },
        ]

        metadata.extend(sample_companies)

        df = pd.DataFrame(metadata)

        # Validate data
        from src.validation import DataValidator

        is_valid, errors = DataValidator.validate_ipo_metadata(df)
        if not is_valid:
            logger.warning(f"Data validation warnings: {errors}")

        # Save to CSV
        output_file = self.data_dir / f"ipo_metadata_{start_year}_{end_year}.csv"
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        logger.info(f"Saved sample IPO metadata to {output_file} ({len(df)} records)")

        return df

    def _collect_krx_metadata(self, start_year: int, end_year: int) -> pd.DataFrame:
        """
        Collect IPO metadata from KRX API

        Note: KRX API only provides basic stock info and daily trade data.
        Additional IPO-specific data (subscription rates, lock-up ratios, etc.)
        needs to be collected from other sources or manually.
        """
        logger.info(f"Collecting IPO metadata from KRX API for {start_year}-{end_year}")

        all_stocks = []

        # Collect stock info for each year
        for year in range(start_year, end_year + 1):
            # Check multiple dates throughout the year to find newly listed stocks
            # Check the last day of each month
            for month in range(1, 13):
                # Get last day of month
                if month == 12:
                    last_day = 31
                else:
                    last_day = (datetime(year, month + 1, 1) - timedelta(days=1)).day

                base_date = f"{year}{month:02d}{last_day:02d}"

                try:
                    stocks = self.krx_client.get_stock_info(base_date)
                    logger.info(f"Retrieved {len(stocks)} stocks for {base_date}")

                    # Filter stocks listed in this year
                    for stock in stocks:
                        list_date = stock.get("LIST_DD", "")
                        if list_date.startswith(str(year)):
                            # Check if already added
                            if not any(
                                s.get("ISU_SRT_CD") == stock.get("ISU_SRT_CD")
                                for s in all_stocks
                            ):
                                all_stocks.append(stock)

                except Exception as e:
                    logger.error(f"Error collecting data for {base_date}: {e}")
                    continue

        logger.info(f"Found {len(all_stocks)} IPO stocks from {start_year}-{end_year}")

        # Convert to DataFrame with our schema
        metadata = []
        for stock in all_stocks:
            # Parse listing date
            list_dd = stock.get("LIST_DD", "")
            try:
                listing_date = datetime.strptime(list_dd, "%Y%m%d").strftime("%Y-%m-%d")
            except:
                listing_date = list_dd

            # Convert LIST_SHRS (상장주식수) - remove commas if present
            list_shrs_str = str(stock.get("LIST_SHRS", "0")).replace(",", "")
            try:
                list_shrs = int(float(list_shrs_str))
            except:
                list_shrs = 0

            # Convert PARVAL (액면가) - remove commas if present
            parval_str = str(stock.get("PARVAL", "0")).replace(",", "")
            try:
                parval = int(float(parval_str))
            except:
                parval = 0

            record = {
                "company_name": stock.get("ISU_NM", ""),
                "code": stock.get("ISU_SRT_CD", ""),
                "listing_date": listing_date,
                # Note: These fields are not available from KRX API
                # They need to be filled from other sources or set to defaults
                "ipo_price_lower": parval,  # Use par value as placeholder
                "ipo_price_upper": parval,
                "ipo_price_confirmed": parval,
                "shares_offered": list_shrs,
                "institutional_demand_rate": 0.0,  # Not available
                "lockup_ratio": 0.0,  # Not available
                "subscription_competition_rate": 0.0,  # Not available
                "paid_in_capital": parval * list_shrs,  # Estimate
                "estimated_market_cap": parval * list_shrs,  # Estimate
                "listing_method": stock.get("MKT_TP_NM", "GENERAL"),
                "allocation_ratio_equal": 50.0,  # Default
                "allocation_ratio_proportional": 50.0,  # Default
                "industry": stock.get("SECT_TP_NM", ""),  # KOSDAQ sector classification
                "theme": stock.get("SECUGRP_NM", ""),  # Security group (주권)
            }
            metadata.append(record)

        df = pd.DataFrame(metadata)

        if len(df) == 0:
            logger.warning("No IPO data found. Using sample data instead.")
            return self._collect_sample_metadata(start_year, end_year)

        # Filter out SPAC companies
        initial_count = len(df)
        df = df[
            (~df["company_name"].str.contains("기업인수목적", na=False))
            & (
                ~df.get("industry", pd.Series([""] * len(df))).str.contains(
                    "SPAC", na=False
                )
            )
        ]
        spac_count = initial_count - len(df)
        if spac_count > 0:
            logger.info(f"Filtered out {spac_count} SPAC companies")

        # Validate data
        from src.validation import DataValidator

        is_valid, errors = DataValidator.validate_ipo_metadata(df)
        if not is_valid:
            logger.warning(f"Data validation warnings: {errors}")

        # Save to CSV
        output_file = self.data_dir / f"ipo_metadata_{start_year}_{end_year}.csv"
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        logger.info(f"Saved KRX IPO metadata to {output_file} ({len(df)} records)")

        return df

    def _collect_krx_metadata_optimized(
        self, start_year: int, end_year: int
    ) -> pd.DataFrame:
        """
        Optimized IPO metadata collection - Single API call

        Instead of checking every month, fetch latest date and filter locally.
        Reduces API calls from 48 (4 years × 12 months) to 1.

        Args:
            start_year: Start year
            end_year: End year

        Returns:
            DataFrame with IPO metadata
        """
        logger.info(f"Collecting IPO metadata (optimized) for {start_year}-{end_year}")

        # Fetch all stocks from latest date
        latest_date = f"{end_year}1231"
        logger.info(f"Fetching all stocks from latest date: {latest_date}")

        try:
            all_stocks = self.krx_client.get_stock_info(latest_date)
            logger.info(f"Retrieved {len(all_stocks)} total stocks")
        except Exception as e:
            logger.error(f"Failed to fetch stock info: {e}")
            logger.warning("Falling back to sample data")
            return self._collect_sample_metadata(start_year, end_year)

        # Filter IPO stocks by listing date (local filtering)
        ipo_stocks = []
        for stock in all_stocks:
            list_date_str = stock.get("LIST_DD", "")
            if not list_date_str:
                continue

            try:
                list_year = int(list_date_str[:4])
                if start_year <= list_year <= end_year:
                    ipo_stocks.append(stock)
            except (ValueError, IndexError):
                continue

        logger.info(
            f"Found {len(ipo_stocks)} IPO stocks from {start_year}-{end_year} "
            f"(filtered locally from {len(all_stocks)} total stocks)"
        )

        if len(ipo_stocks) == 0:
            logger.warning("No IPO stocks found. Using sample data.")
            return self._collect_sample_metadata(start_year, end_year)

        # Convert to DataFrame with our schema
        metadata = []
        for stock in ipo_stocks:
            # Parse listing date
            list_dd = stock.get("LIST_DD", "")
            try:
                listing_date = datetime.strptime(list_dd, "%Y%m%d").strftime("%Y-%m-%d")
            except:
                listing_date = list_dd

            # Convert LIST_SHRS (상장주식수)
            list_shrs_str = str(stock.get("LIST_SHRS", "0")).replace(",", "")
            try:
                list_shrs = int(float(list_shrs_str))
            except:
                list_shrs = 0

            # Convert PARVAL (액면가)
            parval_str = str(stock.get("PARVAL", "0")).replace(",", "")
            try:
                parval = int(float(parval_str))
            except:
                parval = 0

            record = {
                "company_name": stock.get("ISU_NM", ""),
                "code": stock.get("ISU_SRT_CD", ""),
                "listing_date": listing_date,
                "ipo_price_lower": parval,
                "ipo_price_upper": parval,
                "ipo_price_confirmed": parval,
                "shares_offered": list_shrs,
                "institutional_demand_rate": 0.0,
                "lockup_ratio": 0.0,
                "subscription_competition_rate": 0.0,
                "paid_in_capital": parval * list_shrs,
                "estimated_market_cap": parval * list_shrs,
                "listing_method": stock.get("MKT_TP_NM", "GENERAL"),
                "allocation_ratio_equal": 50.0,
                "allocation_ratio_proportional": 50.0,
                "industry": stock.get("SECT_TP_NM", ""),  # KOSDAQ sector classification
                "theme": stock.get("SECUGRP_NM", ""),  # Security group (주권)
            }
            metadata.append(record)

        df = pd.DataFrame(metadata)

        # Filter out SPAC companies
        initial_count = len(df)
        df = df[
            (~df["company_name"].str.contains("기업인수목적", na=False))
            & (
                ~df.get("industry", pd.Series([""] * len(df))).str.contains(
                    "SPAC", na=False
                )
            )
        ]
        spac_count = initial_count - len(df)
        if spac_count > 0:
            logger.info(f"Filtered out {spac_count} SPAC companies")

        # Validate data
        from src.validation import DataValidator

        is_valid, errors = DataValidator.validate_ipo_metadata(df)
        if not is_valid:
            logger.warning(f"Data validation warnings: {errors}")

        # Save to CSV
        output_file = self.data_dir / f"ipo_metadata_{start_year}_{end_year}.csv"
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        logger.info(
            f"Saved KRX IPO metadata (optimized) to {output_file} ({len(df)} records)"
        )

        return df

    def collect_intraday_prices(self, code: str, date: datetime) -> pd.DataFrame:
        """
        Collect intraday execution price data for a specific stock on a specific date

        Returns DataFrame with columns: time, price, volume
        """
        # TODO: Implement actual KRX market data API integration
        # This should fetch tick-by-tick or minute-by-minute execution data

        # Placeholder structure
        intraday_data = []

        # Example: Simulate intraday data
        base_price = 22000
        for hour in range(9, 16):
            for minute in range(0, 60, 5):
                intraday_data.append(
                    {
                        "time": f"{hour:02d}:{minute:02d}",
                        "price": base_price + (hour - 9) * 100 + minute,
                        "volume": 1000,
                    }
                )

        df = pd.DataFrame(intraday_data)

        # Save to CSV
        date_str = date.strftime("%Y%m%d")
        output_file = self.data_dir / f"intraday_{code}_{date_str}.csv"
        df.to_csv(output_file, index=False, encoding="utf-8-sig")

        return df

    def get_highest_and_closing_price(
        self, code: str, date: datetime
    ) -> Dict[str, float]:
        """
        Extract highest execution price and closing price from daily data

        Note: Uses KRX daily trade data for now.
        Intraday tick data will be available via 한국투자 API later.
        """
        if self.use_sample_data:
            # Use sample intraday data
            df = self.collect_intraday_prices(code, date)
            highest_price = df["price"].max()
            closing_price = df.iloc[-1]["price"]
            return {"highest": highest_price, "closing": closing_price}

        # Use KRX daily trade data
        date_str = date.strftime("%Y%m%d")

        try:
            trade_data = self.krx_client.get_daily_trade_by_code(date_str, code)

            if trade_data:
                # Parse prices (remove commas if present)
                high_str = str(trade_data.get("TDD_HGPRC", "0")).replace(",", "")
                close_str = str(trade_data.get("TDD_CLSPRC", "0")).replace(",", "")

                try:
                    highest_price = float(high_str)
                    closing_price = float(close_str)
                except:
                    logger.warning(f"Failed to parse prices for {code} on {date_str}")
                    highest_price = 0.0
                    closing_price = 0.0

                return {"highest": highest_price, "closing": closing_price}
            else:
                logger.warning(f"No trade data found for {code} on {date_str}")
                return {"highest": 0.0, "closing": 0.0}

        except Exception as e:
            logger.error(f"Error getting prices for {code} on {date_str}: {e}")
            return {"highest": 0.0, "closing": 0.0}

    def _collect_prices_batch_optimized(
        self, metadata_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Optimized price data collection - Batch by date

        Instead of calling API for each stock separately, group by date
        and fetch all stocks for that date at once.

        Reduces API calls from 2N (N stocks × 2 days) to unique dates.

        Args:
            metadata_df: DataFrame with IPO metadata including 'code' and 'listing_date'

        Returns:
            DataFrame with added price columns (day0_high, day0_close, day1_high, day1_close)
        """
        logger.info("Collecting price data (batch optimized)")

        # Collect all unique dates needed
        dates_needed: Set[str] = set()
        for _, row in metadata_df.iterrows():
            listing_date = pd.to_datetime(row["listing_date"])
            next_day = listing_date + timedelta(days=1)

            dates_needed.add(listing_date.strftime("%Y%m%d"))
            dates_needed.add(next_day.strftime("%Y%m%d"))

        logger.info(
            f"Need price data for {len(dates_needed)} unique dates "
            f"(for {len(metadata_df)} IPOs)"
        )

        # Check rate limit before proceeding
        if hasattr(self, "krx_client"):
            current_count = self.krx_client.request_count.get("daily_trade", 0)
            if current_count + len(dates_needed) > 9000:
                logger.warning(
                    f"Rate limit warning: {current_count} + {len(dates_needed)} "
                    f"= {current_count + len(dates_needed)} requests"
                )

        # Fetch all trade data for each date (with progress bar)
        date_trade_data = {}

        for date_str in tqdm(
            sorted(dates_needed), desc="Fetching price data", unit="date"
        ):
            try:
                # Check checkpoint
                checkpoint = self.cache_manager.load_checkpoint()
                if checkpoint and date_str in checkpoint.get("completed_dates", []):
                    logger.debug(f"Skipping {date_str} (already completed)")
                    continue

                trades = self.krx_client.get_daily_trade_data(date_str)
                date_trade_data[date_str] = {
                    trade.get("ISU_CD", ""): trade for trade in trades
                }

                # Save checkpoint periodically (every 10 dates)
                if len(date_trade_data) % 10 == 0:
                    completed_dates = list(date_trade_data.keys())
                    self.cache_manager.save_checkpoint(
                        {
                            "stage": "price_collection",
                            "completed_dates": completed_dates,
                            "total_dates": len(dates_needed),
                        }
                    )

            except Exception as e:
                logger.error(f"Failed to fetch trade data for {date_str}: {e}")
                date_trade_data[date_str] = {}

        # Clear checkpoint after successful completion
        self.cache_manager.clear_checkpoint()

        # Enrich metadata with price data
        enriched_data = []

        for _, row in tqdm(
            metadata_df.iterrows(), desc="Processing IPOs", total=len(metadata_df)
        ):
            code = row["code"]
            listing_date = pd.to_datetime(row["listing_date"])
            next_day = listing_date + timedelta(days=1)

            day0_str = listing_date.strftime("%Y%m%d")
            day1_str = next_day.strftime("%Y%m%d")

            # Extract day 0 prices
            day0_trade = self._extract_trade_for_code(
                date_trade_data.get(day0_str, {}), code
            )
            day0_high = self._parse_price(day0_trade.get("TDD_HGPRC", "0"))
            day0_close = self._parse_price(day0_trade.get("TDD_CLSPRC", "0"))

            # Extract day 1 prices
            day1_trade = self._extract_trade_for_code(
                date_trade_data.get(day1_str, {}), code
            )
            day1_high = self._parse_price(day1_trade.get("TDD_HGPRC", "0"))
            day1_close = self._parse_price(day1_trade.get("TDD_CLSPRC", "0"))

            # Combine all data
            enriched_row = row.to_dict()
            enriched_row.update(
                {
                    "day0_high": day0_high,
                    "day0_close": day0_close,
                    "day1_high": day1_high,
                    "day1_close": day1_close,
                }
            )

            enriched_data.append(enriched_row)

        return pd.DataFrame(enriched_data)

    def _extract_trade_for_code(self, date_trades: Dict, code: str) -> Dict:
        """Extract trade data for a specific stock code from date trades"""
        for isu_cd, trade in date_trades.items():
            if code in isu_cd:  # ISU_CD may contain more than just the short code
                return trade
        return {}

    def _parse_price(self, price_str: str) -> float:
        """Parse price string to float"""
        try:
            return float(str(price_str).replace(",", ""))
        except:
            return 0.0

    def collect_full_dataset(
        self, start_year: int = 2022, end_year: int = 2025, optimized: bool = True
    ) -> pd.DataFrame:
        """
        Collect complete dataset with IPO metadata and price data for both Day 0 and Day 1

        Args:
            start_year: Start year
            end_year: End year
            optimized: Use optimized batch collection (default: True)

        Returns:
            DataFrame with complete IPO data including prices
        """
        logger.info(
            f"Collecting full dataset for {start_year}-{end_year} "
            f"(optimized={optimized})"
        )

        # Get IPO metadata
        metadata_df = self.collect_ipo_metadata(
            start_year, end_year, optimized=optimized
        )

        if self.use_sample_data:
            # For sample data, use legacy method
            enriched_data = []

            for _, row in metadata_df.iterrows():
                code = row["code"]
                listing_date = pd.to_datetime(row["listing_date"])
                next_day = listing_date + timedelta(days=1)

                day0_prices = self.get_highest_and_closing_price(code, listing_date)
                day1_prices = self.get_highest_and_closing_price(code, next_day)

                enriched_row = row.to_dict()
                enriched_row.update(
                    {
                        "day0_high": day0_prices["highest"],
                        "day0_close": day0_prices["closing"],
                        "day1_high": day1_prices["highest"],
                        "day1_close": day1_prices["closing"],
                    }
                )
                enriched_data.append(enriched_row)

            full_df = pd.DataFrame(enriched_data)
        elif optimized:
            # Use batch optimized price collection
            full_df = self._collect_prices_batch_optimized(metadata_df)
        else:
            # Use legacy method (one API call per stock)
            enriched_data = []

            for _, row in tqdm(
                metadata_df.iterrows(),
                desc="Collecting prices",
                total=len(metadata_df),
            ):
                code = row["code"]
                listing_date = pd.to_datetime(row["listing_date"])
                next_day = listing_date + timedelta(days=1)

                day0_prices = self.get_highest_and_closing_price(code, listing_date)
                day1_prices = self.get_highest_and_closing_price(code, next_day)

                enriched_row = row.to_dict()
                enriched_row.update(
                    {
                        "day0_high": day0_prices["highest"],
                        "day0_close": day0_prices["closing"],
                        "day1_high": day1_prices["highest"],
                        "day1_close": day1_prices["closing"],
                    }
                )
                enriched_data.append(enriched_row)

            full_df = pd.DataFrame(enriched_data)

        # Save complete dataset
        output_file = self.data_dir / f"ipo_full_dataset_{start_year}_{end_year}.csv"
        full_df.to_csv(output_file, index=False, encoding="utf-8-sig")
        logger.info(
            f"Saved full dataset to {output_file} ({len(full_df)} records with price data)"
        )

        return full_df


if __name__ == "__main__":
    # Use sample data by default (set use_sample_data=False to use KRX API)
    collector = IPODataCollector(use_sample_data=True)
    df = collector.collect_full_dataset(2022, 2025)
    print(f"Collected data for {len(df)} IPOs")
    print(df.head())
