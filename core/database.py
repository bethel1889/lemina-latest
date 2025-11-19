"""
database layer for supabase operations
"""

import os
import json
import logging
from typing import List, Optional, Dict
from datetime import date, datetime
from supabase import create_client, Client
from core.models import Company, FundingRound, CompanyUpdate
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# load env
load_dotenv('.env.local')


class Database:
    """handle all supabase database operations"""

    def __init__(self):
        url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not url or not key:
            raise ValueError("missing supabase credentials in .env.local")

        self.client: Client = create_client(url, key)
        logger.info("connected to supabase")

    def insert_aggregated_data(self, aggregated: Dict) -> Dict:
        """insert companies and related data"""
        companies = aggregated.get('companies', [])
        funding_rounds = aggregated.get('funding_rounds', [])
        company_updates = aggregated.get('company_updates', [])

        stats = {
            'companies_inserted': 0,
            'companies_updated': 0,
            'funding_rounds_inserted': 0,
            'updates_inserted': 0,
            'errors': 0,
        }

        logger.info(f"inserting {len(companies)} companies...")

        for company in companies:
            try:
                # upsert company
                company_id, is_new = self._upsert_company(company)

                if company_id:
                    if is_new:
                        stats['companies_inserted'] += 1
                    else:
                        stats['companies_updated'] += 1

                    # insert related data
                    stats['funding_rounds_inserted'] += self._insert_funding_rounds(
                        company_id, funding_rounds, company.name
                    )
                    stats['updates_inserted'] += self._insert_company_updates(
                        company_id, company_updates, company.name
                    )

                    logger.info(f"  ✓ {company.name} (id={company_id})")

            except Exception as e:
                logger.error(f"  ✗ failed to insert {company.name}: {e}")
                stats['errors'] += 1
                continue

        logger.info(f"database insertion complete: {stats}")
        return stats

    def _upsert_company(self, company: Company) -> tuple[Optional[int], bool]:
        """insert or update company, return (company_id, is_new)"""
        # check if exists by website
        existing = None
        if company.website:
            try:
                result = self.client.table('companies')\
                    .select('id')\
                    .eq('website', company.website)\
                    .execute()
                existing = result.data[0] if result.data else None
            except Exception as e:
                logger.warning(f"failed to check existing company by website: {e}")

        # if no website match, try by name
        if not existing:
            try:
                result = self.client.table('companies')\
                    .select('id')\
                    .eq('name', company.name)\
                    .execute()
                existing = result.data[0] if result.data else None
            except Exception as e:
                logger.warning(f"failed to check existing company by name: {e}")

        # prepare data
        data = {
            'name': company.name,
            'website': company.website,
            'sector': company.sector,
            'sub_sector': company.sub_sector,
            'business_model': company.business_model,
            'short_description': company.short_description,
            'long_description': company.long_description,
            'founded_year': company.founded_year,
            'team_size': company.team_size,
            'founders': json.dumps(company.founders) if company.founders else None,
            'headquarters': company.headquarters,
            'linkedin_url': company.linkedin_url,
            'twitter_url': company.twitter_url,
            'crunchbase_url': company.crunchbase_url,
            'verification_status': company.verification_status,
            'data_quality_score': company.data_quality_score,
            'cac_verified': company.cac_verified,
            'cbn_licensed': company.cbn_licensed,
            'sec_registered': company.sec_registered,
            'naicom_licensed': company.naicom_licensed,
            'last_verified_date': date.today().isoformat(),
            'created_by': 'scraper',
            'updated_at': datetime.now().isoformat(),
        }

        if existing:
            # update existing
            result = self.client.table('companies')\
                .update(data)\
                .eq('id', existing['id'])\
                .execute()
            return existing['id'], False
        else:
            # insert new
            data['created_at'] = datetime.now().isoformat()
            result = self.client.table('companies')\
                .insert(data)\
                .execute()

            if result.data:
                return result.data[0]['id'], True
            else:
                return None, False

    def _insert_funding_rounds(self, company_id: int,
                                all_rounds: List[FundingRound],
                                company_name: str) -> int:
        """insert funding rounds for company"""
        company_rounds = [r for r in all_rounds if r.company_name == company_name]

        if not company_rounds:
            return 0

        inserted = 0
        for round_data in company_rounds:
            try:
                # convert date to string if needed
                announced_date = round_data.announced_date
                if announced_date:
                    if isinstance(announced_date, str):
                        announced_date_str = announced_date
                    else:
                        announced_date_str = announced_date.isoformat()
                else:
                    announced_date_str = None

                data = {
                    'company_id': company_id,
                    'round_type': round_data.round_type,
                    'round_name': round_data.round_name,
                    'amount': float(round_data.amount) if round_data.amount else None,
                    'currency': round_data.currency,
                    'amount_usd': float(round_data.amount_usd) if round_data.amount_usd else None,
                    'is_disclosed': round_data.is_disclosed,
                    'announced_date': announced_date_str,
                    'lead_investors': ','.join(round_data.lead_investors) if round_data.lead_investors else None,
                    'participating_investors': ','.join(round_data.participating_investors) if round_data.participating_investors else None,
                    'source': round_data.source,
                    'source_url': round_data.source_url,
                    'verified': len(round_data.lead_investors) > 0,
                }

                self.client.table('funding_rounds').insert(data).execute()
                inserted += 1

            except Exception as e:
                logger.error(f"failed to insert funding round: {e}")
                continue

        return inserted

    def _insert_company_updates(self, company_id: int,
                                 all_updates: List[CompanyUpdate],
                                 company_name: str) -> int:
        """insert company updates for company"""
        company_updates = [u for u in all_updates if u.company_name == company_name]

        if not company_updates:
            return 0

        inserted = 0
        for update in company_updates:
            try:
                # convert date to string if needed
                update_date = update.update_date
                if update_date:
                    if isinstance(update_date, str):
                        update_date_str = update_date
                    else:
                        update_date_str = update_date.isoformat()
                else:
                    update_date_str = date.today().isoformat()

                data = {
                    'company_id': company_id,
                    'update_type': update.update_type,
                    'title': update.title,
                    'description': update.description,
                    'source_name': update.source_name,
                    'source_url': update.source_url,
                    'update_date': update_date_str,
                }

                self.client.table('company_updates').insert(data).execute()
                inserted += 1

            except Exception as e:
                logger.error(f"failed to insert company update: {e}")
                continue

        return inserted
