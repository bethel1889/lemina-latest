"""
extract funding information from articles
"""

import re
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
from extractors.parsers.amount_parser import AmountParser
from extractors.parsers.date_parser import DateParser


class FundingExtractor:
    """extract funding round data from articles"""

    @classmethod
    def extract(cls, soup: BeautifulSoup, company_name: str) -> Optional[Dict]:
        """
        extract funding information from article
        returns dict with funding details or none
        """
        # get full text
        text = soup.get_text()

        # check if article is about funding
        if not cls._is_funding_article(text):
            return None

        # extract amount
        amount_data = AmountParser.parse(text)
        if not amount_data:
            # might be undisclosed
            if 'undisclosed' in text.lower():
                amount = None
                currency = 'usd'
                is_disclosed = False
            else:
                return None
        else:
            amount, currency = amount_data
            is_disclosed = True

        # extract round type
        round_type = AmountParser.extract_round_type(text)
        if not round_type:
            round_type = 'seed'

        # extract investors
        investors = cls._extract_investors(text)

        # extract date
        announced_date = cls._extract_date(soup, text)

        return {
            'company_name': company_name,
            'round_type': round_type,
            'amount': amount,
            'currency': currency,
            'is_disclosed': is_disclosed,
            'announced_date': announced_date,
            'lead_investors': investors.get('lead', []),
            'participating_investors': investors.get('participating', []),
        }

    @classmethod
    def _is_funding_article(cls, text: str) -> bool:
        """check if article is about funding"""
        text_lower = text.lower()

        funding_keywords = [
            'raises', 'raised', 'secures', 'secured', 'funding', 'investment',
            'round', 'series', 'seed', 'pre-seed', 'investors', 'invested'
        ]

        return any(keyword in text_lower for keyword in funding_keywords)

    @classmethod
    def _extract_investors(cls, text: str) -> Dict[str, List[str]]:
        """extract investor names"""
        investors = {'lead': [], 'participating': []}

        # patterns for investors
        lead_patterns = [
            r'led by ([A-Z][a-zA-Z\s&,]+(?:Capital|Ventures|Partners|Fund|VC|Investments?))',
            r'lead investors?\s+(?:include|are|is)\s+([A-Z][a-zA-Z\s&,]+)',
        ]

        for pattern in lead_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # split by commas and "and"
                names = re.split(r',\s*(?:and\s+)?|\s+and\s+', match)
                for name in names:
                    name = name.strip()
                    if len(name) > 2:
                        investors['lead'].append(name)

        # participating investors
        participating_patterns = [
            r'participating investors?\s+(?:include|are)\s+([A-Z][a-zA-Z\s&,]+)',
            r'joined by ([A-Z][a-zA-Z\s&,]+(?:Capital|Ventures|Partners|Fund))',
        ]

        for pattern in participating_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                names = re.split(r',\s*(?:and\s+)?|\s+and\s+', match)
                for name in names:
                    name = name.strip()
                    if len(name) > 2 and name not in investors['lead']:
                        investors['participating'].append(name)

        return investors

    @classmethod
    def _extract_date(cls, soup: BeautifulSoup, text: str) -> Optional[str]:
        """extract announcement date"""
        # try to get publish date from meta tags
        date_meta = soup.find('meta', attrs={'property': 'article:published_time'})
        if date_meta and date_meta.get('content'):
            parsed = DateParser.parse(date_meta['content'])
            if parsed:
                return parsed.isoformat()

        # try time tag
        time_tag = soup.find('time', datetime=True)
        if time_tag:
            parsed = DateParser.parse(time_tag['datetime'])
            if parsed:
                return parsed.isoformat()

        # fallback to parsing from text
        date_patterns = [
            r'(?:announced|raised|secured)\s+(?:on\s+)?([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                parsed = DateParser.parse(match.group(1))
                if parsed:
                    return parsed.isoformat()

        return None
