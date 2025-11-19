"""
parse funding amounts from text
"""

import re
from decimal import Decimal
from typing import Optional, Tuple


class AmountParser:
    """extract and parse monetary amounts"""

    # regex patterns for amounts
    AMOUNT_PATTERNS = [
        r'\$(\d+(?:\.\d+)?)\s*(million|m|mn)',
        r'\$(\d+(?:\.\d+)?)\s*(billion|b|bn)',
        r'\$(\d+(?:\.\d+)?)\s*(thousand|k)',
        r'(\d+(?:\.\d+)?)\s*million\s*(?:dollars|usd)',
        r'(\d+(?:\.\d+)?)\s*billion\s*(?:dollars|usd)',
        r'ngn\s*(\d+(?:\.\d+)?)\s*(million|m|mn)',
        r'ngn\s*(\d+(?:\.\d+)?)\s*(billion|b|bn)',
        r'₦(\d+(?:\.\d+)?)\s*(million|m|mn)',
        r'₦(\d+(?:\.\d+)?)\s*(billion|b|bn)',
    ]

    MULTIPLIERS = {
        'thousand': 1_000,
        'k': 1_000,
        'million': 1_000_000,
        'm': 1_000_000,
        'mn': 1_000_000,
        'billion': 1_000_000_000,
        'b': 1_000_000_000,
        'bn': 1_000_000_000,
    }

    @classmethod
    def parse(cls, text: str) -> Optional[Tuple[Decimal, str]]:
        """
        extract amount and currency from text
        returns (amount, currency) or none
        """
        if not text:
            return None

        text_lower = text.lower()

        # check for undisclosed
        if 'undisclosed' in text_lower:
            return None

        # try each pattern
        for pattern in cls.AMOUNT_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                amount_str = match.group(1)
                unit = match.group(2) if len(match.groups()) > 1 else 'million'

                try:
                    amount = Decimal(amount_str)
                    multiplier = cls.MULTIPLIERS.get(unit.lower(), 1)
                    final_amount = amount * multiplier

                    # determine currency
                    currency = 'usd'
                    if 'ngn' in text_lower or '₦' in text:
                        currency = 'ngn'

                    return (final_amount, currency)

                except (ValueError, ArithmeticError):
                    continue

        return None

    @classmethod
    def extract_round_type(cls, text: str) -> Optional[str]:
        """extract funding round type from text"""
        if not text:
            return None

        text_lower = text.lower()

        # patterns for round types
        round_types = {
            'pre-seed': ['pre-seed', 'preseed', 'pre seed'],
            'seed': ['seed round', 'seed funding', ' seed '],
            'series_a': ['series a', 'series-a'],
            'series_b': ['series b', 'series-b'],
            'series_c': ['series c', 'series-c'],
            'series_d': ['series d', 'series-d'],
            'grant': ['grant', 'awarded'],
            'debt': ['debt financing', 'debt round', 'debt'],
        }

        for round_type, patterns in round_types.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return round_type

        # default to seed if we see "raises" or "secures" but no specific round
        if any(word in text_lower for word in ['raises', 'secures', 'funding']):
            return 'seed'

        return None
