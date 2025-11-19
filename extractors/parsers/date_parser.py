"""
parse dates from text
"""

from dateutil import parser as date_parser
from datetime import date, datetime
from typing import Optional
import re


class DateParser:
    """extract and parse dates from text"""

    @classmethod
    def parse(cls, text: str) -> Optional[date]:
        """extract date from text"""
        if not text:
            return None

        try:
            # try dateutil parser first
            parsed = date_parser.parse(text, fuzzy=True)
            return parsed.date()
        except (ValueError, OverflowError):
            pass

        # try specific patterns
        patterns = [
            r'(\d{4})',  # just year
            r'in (\d{4})',  # "in 2020"
            r'founded in (\d{4})',  # "founded in 2019"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    year = int(match.group(1))
                    if 1990 <= year <= 2030:
                        return date(year, 1, 1)
                except ValueError:
                    continue

        return None

    @classmethod
    def extract_year(cls, text: str) -> Optional[int]:
        """extract just the year from text"""
        if not text:
            return None

        # look for 4-digit years
        match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
        if match:
            year = int(match.group(1))
            if 1990 <= year <= 2030:
                return year

        return None
