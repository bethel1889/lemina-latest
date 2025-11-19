"""
unified data models for all scrapers
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import date, datetime


@dataclass
class Company:
    """unified company model"""
    name: str
    website: Optional[str] = None
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    business_model: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    founded_year: Optional[int] = None
    team_size: Optional[int] = None
    founders: List[str] = field(default_factory=list)
    headquarters: str = "lagos, nigeria"

    # social/data profiles
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    crunchbase_url: Optional[str] = None

    # metadata
    sources: List[str] = field(default_factory=list)
    source_urls: Dict[str, str] = field(default_factory=dict)
    verification_status: str = 'unverified'
    data_quality_score: int = 0

    # regulatory
    cac_verified: bool = False
    cbn_licensed: bool = False
    sec_registered: bool = False
    naicom_licensed: bool = False

    def add_source(self, source_name: str, source_url: str = ''):
        """add a source and update verification status"""
        if source_name not in self.sources:
            self.sources.append(source_name)
            self.source_urls[source_name] = source_url
            self._update_verification_status()

    def _update_verification_status(self):
        """calculate verification based on source count"""
        count = len(self.sources)
        if count >= 3:
            self.verification_status = 'verified'
        elif count == 2:
            self.verification_status = 'cross_referenced'
        elif count == 1:
            self.verification_status = 'self_reported'
        else:
            self.verification_status = 'unverified'

    def merge_with(self, other: 'Company'):
        """merge data from another company instance"""
        # merge descriptions (keep longer one)
        if other.long_description and (
            not self.long_description or
            len(other.long_description) > len(self.long_description)
        ):
            self.long_description = other.long_description

        if other.short_description and not self.short_description:
            self.short_description = other.short_description

        # merge founders (union)
        self.founders = list(set(self.founders + other.founders))

        # add sources
        for source in other.sources:
            self.add_source(source, other.source_urls.get(source, ''))

        # keep most specific sector
        if other.sub_sector and not self.sub_sector:
            self.sub_sector = other.sub_sector

        # fill missing fields
        for field_name in ['website', 'founded_year', 'team_size', 'linkedin_url',
                          'twitter_url', 'sector', 'business_model']:
            if getattr(other, field_name) and not getattr(self, field_name):
                setattr(self, field_name, getattr(other, field_name))

        # merge regulatory flags (or operation)
        self.cac_verified = self.cac_verified or other.cac_verified
        self.cbn_licensed = self.cbn_licensed or other.cbn_licensed
        self.sec_registered = self.sec_registered or other.sec_registered
        self.naicom_licensed = self.naicom_licensed or other.naicom_licensed


@dataclass
class FundingRound:
    """unified funding round model"""
    company_name: str
    round_type: str
    round_name: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: str = 'usd'
    amount_usd: Optional[Decimal] = None
    is_disclosed: bool = True
    announced_date: Optional[date] = None
    lead_investors: List[str] = field(default_factory=list)
    participating_investors: List[str] = field(default_factory=list)
    source: str = ''
    source_url: str = ''

    company_id: Optional[int] = None


@dataclass
class Metric:
    """unified metrics model"""
    company_name: str
    metric_type: str
    value: Decimal
    currency: Optional[str] = None
    unit: Optional[str] = None
    period_type: Optional[str] = None
    period_date: Optional[date] = None
    source: str = ''
    source_url: str = ''
    confidence_level: str = 'low'

    company_id: Optional[int] = None


@dataclass
class RegulatoryInfo:
    """unified regulatory info model"""
    company_name: str
    license_type: str
    license_number: Optional[str] = None
    status: str = 'unknown'
    issue_date: Optional[date] = None
    verified: bool = False
    verification_source: Optional[str] = None

    company_id: Optional[int] = None


@dataclass
class CompanyUpdate:
    """unified company update/news model"""
    company_name: str
    update_type: str
    title: str
    description: Optional[str] = None
    source_name: str = ''
    source_url: str = ''
    update_date: Optional[date] = None

    company_id: Optional[int] = None
