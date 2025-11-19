"""
deduplication utilities for fuzzy matching
"""

from difflib import SequenceMatcher
import re
from urllib.parse import urlparse


class NameNormalizer:
    """normalize company names and urls for matching"""

    @staticmethod
    def normalize_name(name: str) -> str:
        """normalize company name for comparison"""
        if not name:
            return ""

        # lowercase
        normalized = name.lower().strip()

        # remove common suffixes
        suffixes = [
            ' limited', ' ltd', ' inc', ' incorporated', ' corp', ' corporation',
            ' llc', ' plc', ' ng', ' nigeria'
        ]
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()

        # remove special characters except spaces
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)

        # collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized.strip()

    @staticmethod
    def normalize_url(url: str) -> str:
        """normalize url for comparison"""
        if not url:
            return ""

        # parse url
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path

        # remove www prefix
        domain = domain.lower().strip()
        if domain.startswith('www.'):
            domain = domain[4:]

        # remove trailing slash
        domain = domain.rstrip('/')

        return domain


class Deduplicator:
    """fuzzy matching for finding duplicates"""

    @staticmethod
    def calculate_similarity(name1: str, name2: str) -> float:
        """calculate similarity score between two names (0-1)"""
        if not name1 or not name2:
            return 0.0

        # tokenize and sort for better matching of reordered words
        tokens1 = sorted(name1.lower().split())
        tokens2 = sorted(name2.lower().split())

        str1 = ' '.join(tokens1)
        str2 = ' '.join(tokens2)

        # use sequence matcher from difflib
        matcher = SequenceMatcher(None, str1, str2)
        score = matcher.ratio()

        return score

    @staticmethod
    def is_match(name1: str, name2: str, threshold: float = 0.90) -> bool:
        """check if two names match above threshold"""
        similarity = Deduplicator.calculate_similarity(name1, name2)
        return similarity >= threshold
