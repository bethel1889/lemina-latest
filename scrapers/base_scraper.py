"""
base scraper class for all scrapers
"""

from abc import ABC, abstractmethod
from typing import List, Dict
import json
import logging
from datetime import datetime
from utils.http_client import HTTPClient


class BaseScraper(ABC):
    """abstract base class for all scrapers"""

    def __init__(self, config: Dict):
        self.name = self.__class__.__name__
        self.config = config
        self.http = HTTPClient(
            retry_count=config.get('retries', 3),
            rate_limit=config.get('rate_limit', 2.0)
        )
        self.logger = self._setup_logger()
        self.results = []

    def _setup_logger(self):
        """setup logger for this scraper"""
        logger = logging.getLogger(f"scraper.{self.name}")
        logger.setLevel(logging.INFO)

        # console handler
        if not logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter('%(name)s | %(message)s')
            ch.setFormatter(formatter)
            logger.addHandler(ch)

        return logger

    @abstractmethod
    def scrape(self) -> List[Dict]:
        """main scraping logic - must be implemented by subclasses"""
        pass

    def is_enabled(self) -> bool:
        """check if scraper is enabled"""
        return self.config.get('enabled', True)

    def get_priority(self) -> int:
        """get scraper priority (lower = higher priority)"""
        return self.config.get('priority', 99)

    def log_error(self, error: Exception, context: Dict = None):
        """log error to source-specific error file"""
        error_file = f"data/errors/{self.name}_errors.log"
        try:
            with open(error_file, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} | {error} | {context}\n")
        except Exception as e:
            self.logger.error(f"failed to log error: {e}")

    def save_raw_data(self, data: List[Dict]):
        """save raw scraper output"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/raw/{self.name}_{timestamp}.json"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            self.logger.info(f"saved raw data to {output_file}")
        except Exception as e:
            self.logger.error(f"failed to save raw data: {e}")

    def add_result(self, data: Dict):
        """add a result to the collection"""
        if data and data.get('name'):
            self.results.append(data)
