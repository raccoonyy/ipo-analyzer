"""
Cache Manager for KRX API Responses
Manages caching of API responses and checkpoints for resumable data collection
"""

import json
import pickle
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of API responses and collection checkpoints"""

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.cache_dir / "checkpoint.json"
        logger.info(f"Initialized CacheManager with cache_dir: {self.cache_dir}")

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key"""
        # Sanitize key for filename
        safe_key = cache_key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.pkl"

    def get(self, cache_key: str) -> Optional[Any]:
        """
        Get cached data by key

        Args:
            cache_key: Unique key for cached data

        Returns:
            Cached data or None if not found
        """
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            logger.debug(f"Cache miss: {cache_key}")
            return None

        try:
            with open(cache_path, "rb") as f:
                data = pickle.load(f)
            logger.debug(f"Cache hit: {cache_key}")
            return data
        except Exception as e:
            logger.warning(f"Failed to load cache {cache_key}: {e}")
            return None

    def set(self, cache_key: str, data: Any) -> None:
        """
        Save data to cache

        Args:
            cache_key: Unique key for cached data
            data: Data to cache (must be picklable)
        """
        cache_path = self._get_cache_path(cache_key)

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(data, f)
            logger.debug(f"Cached: {cache_key}")
        except Exception as e:
            logger.error(f"Failed to save cache {cache_key}: {e}")

    def has(self, cache_key: str) -> bool:
        """Check if cache exists for key"""
        return self._get_cache_path(cache_key).exists()

    def delete(self, cache_key: str) -> None:
        """Delete cached data by key"""
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Deleted cache: {cache_key}")

    def clear_all(self) -> int:
        """
        Clear all cached data (except checkpoint)

        Returns:
            Number of files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
            count += 1

        logger.info(f"Cleared {count} cache files")
        return count

    def save_checkpoint(self, checkpoint_data: Dict) -> None:
        """
        Save checkpoint for resumable collection

        Args:
            checkpoint_data: Dictionary with checkpoint information
                Example: {
                    'stage': 'price_collection',
                    'completed_dates': ['20240101', '20240102'],
                    'total_dates': 100,
                    'timestamp': '2024-10-07T10:30:00'
                }
        """
        checkpoint_data["timestamp"] = datetime.now().isoformat()

        try:
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved checkpoint: {checkpoint_data.get('stage')}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def load_checkpoint(self) -> Optional[Dict]:
        """
        Load checkpoint data

        Returns:
            Checkpoint dictionary or None if not found
        """
        if not self.checkpoint_file.exists():
            logger.debug("No checkpoint found")
            return None

        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            logger.info(f"Loaded checkpoint: {checkpoint.get('stage')}")
            return checkpoint
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None

    def clear_checkpoint(self) -> None:
        """Delete checkpoint file"""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            logger.info("Cleared checkpoint")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "cache_count": len(cache_files),
            "total_size_mb": total_size / (1024 * 1024),
            "has_checkpoint": self.checkpoint_file.exists(),
        }

    def generate_date_cache_key(self, api_name: str, date: str) -> str:
        """
        Generate cache key for date-based API calls

        Args:
            api_name: API name (e.g., 'stock_info', 'daily_trade')
            date: Date string (YYYYMMDD format)

        Returns:
            Cache key string
        """
        return f"{api_name}_{date}"

    def generate_stock_cache_key(self, api_name: str, code: str, date: str) -> str:
        """
        Generate cache key for stock-specific API calls

        Args:
            api_name: API name
            code: Stock code
            date: Date string

        Returns:
            Cache key string
        """
        return f"{api_name}_{code}_{date}"
