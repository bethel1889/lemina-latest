"""
http client with retry logic and rate limiting
"""

import requests
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class HTTPClient:
    """http client with retry and rate limiting"""

    def __init__(self, retry_count: int = 3, rate_limit: float = 2.0):
        self.retry_count = retry_count
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get(self, url: str, timeout: int = 10) -> Optional[str]:
        """get request with retry logic"""
        for attempt in range(self.retry_count):
            try:
                # rate limiting
                elapsed = time.time() - self.last_request_time
                if elapsed < self.rate_limit:
                    time.sleep(self.rate_limit - elapsed)

                response = self.session.get(url, timeout=timeout)
                self.last_request_time = time.time()

                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:
                    # rate limited, wait longer
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(f"rate limited on {url}, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.warning(f"http {response.status_code} for {url}")
                    return None

            except requests.exceptions.Timeout:
                logger.warning(f"timeout on {url}, attempt {attempt + 1}/{self.retry_count}")
                time.sleep(2 ** attempt)
                continue
            except requests.exceptions.ConnectionError:
                logger.warning(f"connection error on {url}, attempt {attempt + 1}/{self.retry_count}")
                time.sleep(2 ** attempt)
                continue
            except Exception as e:
                logger.error(f"error fetching {url}: {e}")
                return None

        logger.error(f"failed to fetch {url} after {self.retry_count} attempts")
        return None
