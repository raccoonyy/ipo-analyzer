"""
Logging Configuration
Setup logging for the IPO Analyzer backend
"""

import logging
import logging.config
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: str = "logs/ipo_analyzer.log") -> None:
    """
    Setup logging configuration

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": level,
                "formatter": "detailed",
                "filename": log_file,
                "mode": "a",
            },
        },
        "root": {"level": level, "handlers": ["console", "file"]},
        "loggers": {
            "src": {"level": level, "handlers": ["console", "file"], "propagate": False}
        },
    }

    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized with level={level}, log_file={log_file}")
