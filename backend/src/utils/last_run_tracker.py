"""
Last Run Tracker
Track last execution time for incremental data collection
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LastRunTracker:
    """Track last execution time for data collection scripts"""

    def __init__(self, tracker_file: str = "data/.last_run.json"):
        """
        Initialize tracker

        Args:
            tracker_file: Path to tracker file
        """
        self.tracker_file = Path(tracker_file)
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        """Load tracker data from file"""
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load tracker file: {e}")
                return {}
        return {}

    def _save(self):
        """Save tracker data to file"""
        try:
            with open(self.tracker_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved tracker data to {self.tracker_file}")
        except Exception as e:
            logger.error(f"Failed to save tracker file: {e}")

    def get_last_run(self, script_name: str) -> Optional[date]:
        """
        Get last run date for a script

        Args:
            script_name: Name of the script (e.g., 'collect_full_data')

        Returns:
            Last run date or None if never run
        """
        if script_name in self._data:
            date_str = self._data[script_name].get("last_run_date")
            if date_str:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
        return None

    def update_last_run(self, script_name: str, run_date: Optional[date] = None):
        """
        Update last run date for a script

        Args:
            script_name: Name of the script
            run_date: Date to record (defaults to today)
        """
        if run_date is None:
            run_date = date.today()

        if script_name not in self._data:
            self._data[script_name] = {}

        self._data[script_name]["last_run_date"] = run_date.strftime("%Y-%m-%d")
        self._data[script_name]["last_run_timestamp"] = datetime.now().isoformat()

        self._save()
        logger.info(f"Updated last run for '{script_name}': {run_date}")

    def get_collection_date_range(
        self,
        script_name: str,
        default_start_date: Optional[date] = None
    ) -> tuple[date, date]:
        """
        Get date range for incremental collection

        Args:
            script_name: Name of the script
            default_start_date: Start date if never run before

        Returns:
            (start_date, end_date) tuple
        """
        last_run = self.get_last_run(script_name)
        end_date = date.today()

        if last_run:
            # Collect from day after last run
            start_date = last_run
            logger.info(f"Incremental update: {start_date} to {end_date}")
        else:
            # First run - use default or go back 2 years
            if default_start_date:
                start_date = default_start_date
            else:
                start_date = date(end_date.year - 2, 1, 1)
            logger.info(f"First run: {start_date} to {end_date}")

        return start_date, end_date

    def get_all_runs(self) -> dict:
        """Get all tracked runs"""
        return self._data.copy()

    def reset(self, script_name: Optional[str] = None):
        """
        Reset tracker data

        Args:
            script_name: Script to reset, or None to reset all
        """
        if script_name:
            if script_name in self._data:
                del self._data[script_name]
                logger.info(f"Reset tracker for '{script_name}'")
        else:
            self._data = {}
            logger.info("Reset all tracker data")

        self._save()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    tracker = LastRunTracker()

    # Example 1: Get date range for collection
    start_date, end_date = tracker.get_collection_date_range(
        "collect_full_data",
        default_start_date=date(2022, 1, 1)
    )
    print(f"Collection range: {start_date} to {end_date}")

    # Example 2: Update last run
    tracker.update_last_run("collect_full_data")

    # Example 3: Check next run
    start_date, end_date = tracker.get_collection_date_range("collect_full_data")
    print(f"Next collection range: {start_date} to {end_date}")

    # Example 4: View all runs
    print("\nAll tracked runs:")
    print(json.dumps(tracker.get_all_runs(), indent=2))
