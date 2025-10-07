"""
IPO Data Collection Module
Collects IPO metadata and execution price data from KRX for 2022-2025
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from pathlib import Path


class IPODataCollector:
    """Collects IPO metadata and intraday price data"""

    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def collect_ipo_metadata(
        self, start_year: int = 2022, end_year: int = 2025
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
        """
        # TODO: Implement actual KRX API integration
        # This is a template structure for the data collection

        metadata = []

        # Placeholder: Replace with actual KRX API calls
        # Example structure of collected data
        sample_data = {
            "company_name": "ExampleTech",
            "code": "123456",
            "listing_date": "2024-10-01",
            "ipo_price_lower": 20000,
            "ipo_price_upper": 24000,
            "ipo_price_confirmed": 22000,
            "shares_offered": 1000000,
            "institutional_demand_rate": 850.5,  # %
            "lockup_ratio": 30.0,  # %
            "subscription_competition_rate": 1234.56,  # to 1
            "paid_in_capital": 50000000000,  # KRW
            "estimated_market_cap": 220000000000,  # KRW
            "listing_method": "GENERAL",  # GENERAL, BOOK_BUILDING, etc.
            "allocation_ratio_equal": 50.0,  # %
            "allocation_ratio_proportional": 50.0,  # %
            "industry": "IT",
            "theme": "TECH",
        }

        metadata.append(sample_data)

        df = pd.DataFrame(metadata)

        # Save to CSV
        output_file = self.data_dir / f"ipo_metadata_{start_year}_{end_year}.csv"
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"Saved IPO metadata to {output_file}")

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
        Extract highest execution price and closing price from intraday data
        """
        df = self.collect_intraday_prices(code, date)

        highest_price = df["price"].max()
        closing_price = df.iloc[-1]["price"]  # Last price of the day

        return {"highest": highest_price, "closing": closing_price}

    def collect_full_dataset(
        self, start_year: int = 2022, end_year: int = 2025
    ) -> pd.DataFrame:
        """
        Collect complete dataset with IPO metadata and price data for both Day 0 and Day 1
        """
        # Get IPO metadata
        metadata_df = self.collect_ipo_metadata(start_year, end_year)

        # For each IPO, collect Day 0 and Day 1 price data
        enriched_data = []

        for _, row in metadata_df.iterrows():
            code = row["code"]
            listing_date = pd.to_datetime(row["listing_date"])
            next_day = listing_date + timedelta(days=1)

            # Get Day 0 prices
            day0_prices = self.get_highest_and_closing_price(code, listing_date)

            # Get Day 1 prices
            day1_prices = self.get_highest_and_closing_price(code, next_day)

            # Combine all data
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
        print(f"Saved full dataset to {output_file}")

        return full_df


if __name__ == "__main__":
    collector = IPODataCollector()
    df = collector.collect_full_dataset(2022, 2025)
    print(f"Collected data for {len(df)} IPOs")
    print(df.head())
