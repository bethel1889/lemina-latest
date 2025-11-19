"""
triangulation engine - deduplicate and verify data from multiple sources
"""

from typing import List, Dict
import logging
from core.models import Company, FundingRound, CompanyUpdate
from utils.deduplicator import NameNormalizer, Deduplicator

logger = logging.getLogger(__name__)


class Triangulator:
    """cross-reference and verify data from multiple sources"""

    def __init__(self):
        self.normalizer = NameNormalizer()
        self.deduplicator = Deduplicator()

    def process(self, raw_data: Dict[str, List[Dict]]) -> Dict:
        """
        process raw data from all scrapers
        returns aggregated, deduplicated data
        """
        logger.info("starting triangulation...")

        # step 1: convert raw dicts to company models
        all_companies = self._convert_to_company_models(raw_data)
        logger.info(f"converted {len(all_companies)} raw company records")

        # step 2: deduplicate companies
        unique_companies = self._deduplicate_companies(all_companies)
        logger.info(f"after deduplication: {unique_companies} unique companies")

        # step 3: extract related data (funding, updates)
        funding_rounds = self._extract_funding_rounds(raw_data)
        company_updates = self._extract_company_updates(raw_data)

        # step 4: calculate quality scores
        self._calculate_quality_scores(unique_companies)

        logger.info("triangulation complete")

        return {
            'companies': unique_companies,
            'funding_rounds': funding_rounds,
            'company_updates': company_updates,
        }

    def _convert_to_company_models(self, raw_data: Dict[str, List[Dict]]) -> List[Company]:
        """convert raw dicts to company model objects"""
        companies = []

        for source_name, records in raw_data.items():
            for record in records:
                try:
                    company = Company(
                        name=record.get('name', ''),
                        website=record.get('website'),
                        sector=record.get('sector'),
                        sub_sector=record.get('sub_sector'),
                        short_description=record.get('short_description'),
                        long_description=record.get('long_description'),
                        founders=record.get('founders', []),
                    )

                    # add source
                    company.add_source(record.get('source', source_name),
                                     record.get('source_url', ''))

                    companies.append(company)

                except Exception as e:
                    logger.error(f"failed to convert record: {e}")
                    continue

        return companies

    def _deduplicate_companies(self, companies: List[Company]) -> List[Company]:
        """merge duplicate companies from different sources"""
        unique = {}

        for company in companies:
            # find if match exists
            match_key = self._find_match(company, unique)

            if match_key:
                # merge with existing
                unique[match_key].merge_with(company)
                logger.debug(f"merged {company.name} with existing")
            else:
                # add as new
                key = self._get_company_key(company)
                unique[key] = company
                logger.debug(f"added new company: {company.name}")

        return list(unique.values())

    def _find_match(self, company: Company, existing: Dict) -> str:
        """find matching company in existing dict"""
        # exact website match (primary method)
        if company.website:
            normalized_website = self.normalizer.normalize_url(company.website)
            for key, existing_company in existing.items():
                if existing_company.website:
                    existing_normalized = self.normalizer.normalize_url(
                        existing_company.website
                    )
                    if normalized_website == existing_normalized:
                        return key

        # fuzzy name match (> 90% similarity)
        normalized_name = self.normalizer.normalize_name(company.name)
        for key, existing_company in existing.items():
            existing_normalized = self.normalizer.normalize_name(
                existing_company.name
            )
            similarity = self.deduplicator.calculate_similarity(
                normalized_name,
                existing_normalized
            )
            if similarity > 0.90:
                logger.debug(f"fuzzy match: {company.name} ~ {existing_company.name} ({similarity:.2f})")
                return key

        return None

    def _get_company_key(self, company: Company) -> str:
        """generate unique key for company"""
        if company.website:
            return self.normalizer.normalize_url(company.website)
        else:
            return self.normalizer.normalize_name(company.name)

    def _extract_funding_rounds(self, raw_data: Dict[str, List[Dict]]) -> List[FundingRound]:
        """extract funding rounds from raw data"""
        funding_rounds = []

        for source_name, records in raw_data.items():
            for record in records:
                funding_data = record.get('funding')
                if funding_data:
                    try:
                        funding_round = FundingRound(
                            company_name=record.get('name'),
                            round_type=funding_data.get('round_type', 'seed'),
                            round_name=funding_data.get('round_name'),
                            amount=funding_data.get('amount'),
                            currency=funding_data.get('currency', 'usd'),
                            amount_usd=funding_data.get('amount_usd'),
                            is_disclosed=funding_data.get('is_disclosed', True),
                            announced_date=funding_data.get('announced_date'),
                            lead_investors=funding_data.get('lead_investors', []),
                            participating_investors=funding_data.get('participating_investors', []),
                            source=record.get('source', source_name),
                            source_url=record.get('source_url', ''),
                        )
                        funding_rounds.append(funding_round)
                    except Exception as e:
                        logger.error(f"failed to extract funding round: {e}")
                        continue

        logger.info(f"extracted {len(funding_rounds)} funding rounds")
        return funding_rounds

    def _extract_company_updates(self, raw_data: Dict[str, List[Dict]]) -> List[CompanyUpdate]:
        """extract company updates/news from raw data"""
        updates = []

        for source_name, records in raw_data.items():
            for record in records:
                try:
                    # determine update type
                    update_type = 'news'
                    if record.get('funding'):
                        update_type = 'funding'

                    # create update from article
                    update = CompanyUpdate(
                        company_name=record.get('name'),
                        update_type=update_type,
                        title=f"{record.get('name')} - {source_name} article",
                        description=record.get('short_description'),
                        source_name=record.get('source', source_name),
                        source_url=record.get('source_url', ''),
                        update_date=None,  # will be set from article date if available
                    )
                    updates.append(update)

                except Exception as e:
                    logger.error(f"failed to create company update: {e}")
                    continue

        logger.info(f"extracted {len(updates)} company updates")
        return updates

    def _calculate_quality_scores(self, companies: List[Company]):
        """calculate data quality score for each company"""
        for company in companies:
            score = 50  # base score

            # completeness bonuses
            if company.website: score += 10
            if company.short_description and len(company.short_description) > 50: score += 5
            if company.long_description: score += 5
            if company.founders: score += 5
            if company.sector and company.sector != 'other': score += 5

            # verification bonuses (based on source count)
            source_count = len(company.sources)
            if source_count >= 3: score += 20
            elif source_count == 2: score += 10
            elif source_count == 1: score += 5

            company.data_quality_score = min(score, 100)
