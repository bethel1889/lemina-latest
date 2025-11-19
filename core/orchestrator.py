"""
orchestrator - master controller that runs everything
"""

import yaml
import logging
from typing import Dict, List
import concurrent.futures
from core.triangulation import Triangulator
from core.database import Database
from scrapers.news.techcabal import TechCabalScraper
from scrapers.news.techpoint import TechpointScraper

logger = logging.getLogger(__name__)


class Orchestrator:
    """master controller for the scraping pipeline"""

    def __init__(self, config_path: str = 'config/scrapers.yaml', dry_run: bool = False):
        self.config = self._load_config(config_path)
        self.dry_run = dry_run
        self.scrapers = self._initialize_scrapers()
        self.triangulator = Triangulator()
        self.db = Database() if not dry_run else None

    def _load_config(self, config_path: str) -> Dict:
        """load configuration from yaml file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"failed to load config: {e}")
            return {}

    def _initialize_scrapers(self) -> Dict:
        """initialize all enabled scrapers"""
        scrapers = {}

        # techcabal
        techcabal_config = self.config.get('news_scrapers', {}).get('techcabal', {})
        if techcabal_config.get('enabled', False):
            scrapers['techcabal'] = TechCabalScraper(techcabal_config)

        # techpoint
        techpoint_config = self.config.get('news_scrapers', {}).get('techpoint', {})
        if techpoint_config.get('enabled', False):
            scrapers['techpoint'] = TechpointScraper(techpoint_config)

        logger.info(f"initialized {len(scrapers)} scrapers: {list(scrapers.keys())}")
        return scrapers

    def run(self):
        """run the full pipeline"""
        logger.info("=" * 60)
        logger.info("LEMINA STARTUP DATA SCRAPER")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("DRY RUN MODE - no database writes")

        # phase 1: run scrapers
        logger.info("\nphase 1: scraping...")
        raw_data = self._run_scrapers()

        if not raw_data or all(len(v) == 0 for v in raw_data.values()):
            logger.error("no data scraped, aborting")
            return

        # phase 2: triangulation
        logger.info("\nphase 2: triangulation...")
        aggregated = self.triangulator.process(raw_data)

        # phase 3: database insertion
        if not self.dry_run:
            logger.info("\nphase 3: database insertion...")
            stats = self.db.insert_aggregated_data(aggregated)
        else:
            logger.info("\nphase 3: skipped (dry run)")
            stats = {'companies_inserted': 0, 'companies_updated': 0}

        # phase 4: summary report
        self._generate_summary_report(aggregated, stats)

    def _run_scrapers(self) -> Dict[str, List[Dict]]:
        """run all enabled scrapers in parallel"""
        results = {}

        max_workers = self.config.get('global_settings', {}).get('max_workers', 3)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}

            for name, scraper in self.scrapers.items():
                future = executor.submit(self._safe_scrape, scraper)
                futures[future] = name

            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                try:
                    results[name] = future.result()
                    logger.info(f"✓ {name} completed: {len(results[name])} records")
                except Exception as e:
                    logger.error(f"✗ {name} failed: {e}")
                    results[name] = []

        return results

    def _safe_scrape(self, scraper):
        """run scraper with error handling"""
        try:
            return scraper.scrape()
        except Exception as e:
            scraper.log_error(e)
            return []

    def _generate_summary_report(self, aggregated: Dict, stats: Dict):
        """generate and print summary report"""
        companies = aggregated.get('companies', [])
        funding_rounds = aggregated.get('funding_rounds', [])
        company_updates = aggregated.get('company_updates', [])

        logger.info("\n" + "=" * 60)
        logger.info("SCRAPING SUMMARY")
        logger.info("=" * 60)

        logger.info(f"\ntotal unique companies: {len(companies)}")

        # verification breakdown
        verified = len([c for c in companies if c.verification_status == 'verified'])
        cross_ref = len([c for c in companies if c.verification_status == 'cross_referenced'])
        self_reported = len([c for c in companies if c.verification_status == 'self_reported'])

        logger.info(f"  - verified (3+ sources): {verified}")
        logger.info(f"  - cross_referenced (2 sources): {cross_ref}")
        logger.info(f"  - self_reported (1 source): {self_reported}")

        # sector breakdown
        sectors = {}
        for company in companies:
            sector = company.sector or 'unknown'
            sectors[sector] = sectors.get(sector, 0) + 1

        logger.info(f"\nsector breakdown:")
        for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  - {sector}: {count}")

        logger.info(f"\nfunding rounds extracted: {len(funding_rounds)}")
        logger.info(f"company updates: {len(company_updates)}")

        # database stats
        if stats:
            logger.info(f"\ndatabase operations:")
            logger.info(f"  - companies inserted: {stats.get('companies_inserted', 0)}")
            logger.info(f"  - companies updated: {stats.get('companies_updated', 0)}")
            logger.info(f"  - funding rounds inserted: {stats.get('funding_rounds_inserted', 0)}")
            logger.info(f"  - errors: {stats.get('errors', 0)}")

        # average quality score
        if companies:
            avg_score = sum(c.data_quality_score for c in companies) / len(companies)
            logger.info(f"\naverage data quality score: {avg_score:.1f}/100")

        logger.info("\n" + "=" * 60)
        logger.info("✓ SCRAPING COMPLETE")
        logger.info("=" * 60)
