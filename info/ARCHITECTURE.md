# lemina scraper architecture

production-grade, scalable data collection system for nigerian startups.

## design principles

1. **plugin-based scrapers** - add new sources without touching core code
2. **single orchestrator** - one command runs everything
3. **config-driven** - enable/disable sources via yaml config
4. **fault-tolerant** - failures in one scraper don't stop others
5. **resumable** - checkpoint system for interrupted runs
6. **observable** - comprehensive logging and metrics
7. **testable** - unit tests, integration tests, dry-run mode

## directory structure

```
lemina-web-scraper/
├── config/
│   ├── scrapers.yaml           # scraper configurations
│   ├── sources.yaml            # source priorities and weights
│   └── settings.yaml           # global settings (rate limits, retries)
│
├── core/
│   ├── orchestrator.py         # master controller
│   ├── models.py               # unified data models
│   ├── triangulation.py        # cross-reference and verify data
│   ├── database.py             # supabase operations
│   ├── progress.py             # checkpoint management
│   └── logging_config.py       # structured logging setup
│
├── scrapers/
│   ├── base_scraper.py         # abstract base class
│   ├── registry.py             # scraper plugin registry
│   │
│   ├── news/                   # news site scrapers
│   │   ├── techcabal.py
│   │   ├── techpoint.py
│   │   ├── disrupt_africa.py
│   │   ├── nairametrics.py
│   │   └── the_big_deal.py
│   │
│   ├── databases/              # structured data sources
│   │   ├── crunchbase.py
│   │   └── vc_blogs.py
│   │
│   ├── regulatory/             # official government sources
│   │   ├── cbn_licenses.py
│   │   ├── cac_registry.py
│   │   └── sec_registry.py
│   │
│   ├── direct/                 # company direct sources
│   │   ├── company_websites.py
│   │   └── linkedin_pages.py
│   │
│   └── metrics/                # traction data sources
│       ├── app_stores.py
│       └── similarweb.py
│
├── extractors/
│   ├── company_extractor.py    # extract company data from text
│   ├── funding_extractor.py    # extract funding info
│   ├── metrics_extractor.py    # extract traction metrics
│   ├── founder_extractor.py    # extract founder data
│   ├── regulatory_extractor.py # extract license info
│   └── parsers/                # specialized parsers
│       ├── amount_parser.py    # parse "$5m", "ngn 2bn"
│       ├── date_parser.py      # parse various date formats
│       └── name_normalizer.py  # normalize company names
│
├── utils/
│   ├── http_client.py          # requests wrapper with retry logic
│   ├── currency_converter.py   # live exchange rates
│   ├── deduplicator.py         # fuzzy matching for duplicates
│   ├── cache.py                # response caching
│   └── validators.py           # data validation helpers
│
├── data/
│   ├── raw/                    # raw scraper output
│   │   ├── techcabal_YYYYMMDD.json
│   │   ├── techpoint_YYYYMMDD.json
│   │   └── ...
│   │
│   ├── processed/              # after triangulation
│   │   └── aggregated_YYYYMMDD.json
│   │
│   ├── checkpoints/            # progress snapshots
│   │   └── progress_YYYYMMDD_HHMMSS.json
│   │
│   └── errors/                 # error logs per source
│       └── techcabal_errors.log
│
├── tests/
│   ├── fixtures/               # sample html/json for testing
│   ├── test_extractors.py
│   ├── test_scrapers.py
│   └── test_triangulation.py
│
├── scripts/
│   ├── scrape.py               # legacy v1 (keep for reference)
│   ├── verify.py               # legacy v1
│   └── insert.py               # legacy v1
│
├── main.py                     # main entry point
├── requirements.txt
├── .env.local                  # credentials
├── CLAUDE.md
├── ARCHITECTURE.md
└── DATA_SOURCES.md
```

## core components

### 1. master orchestrator (core/orchestrator.py)

single entry point that coordinates everything:

```python
class Orchestrator:
    def __init__(self, config_path='config/scrapers.yaml'):
        self.config = load_config(config_path)
        self.scrapers = self._load_scrapers()
        self.db = Database()
        self.progress = ProgressTracker()
        self.triangulator = Triangulator()

    def run(self, resume=False):
        """run full pipeline"""
        if resume:
            self.progress.load_checkpoint()

        # phase 1: scraping
        raw_data = self._run_scrapers()

        # phase 2: triangulation
        aggregated = self.triangulator.process(raw_data)

        # phase 3: database insertion
        self._insert_to_database(aggregated)

        # phase 4: generate report
        self._generate_summary_report()

    def _run_scrapers(self):
        """run all enabled scrapers in parallel"""
        results = {}

        # group scrapers by type for parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}

            for name, scraper in self.scrapers.items():
                if scraper.is_enabled():
                    future = executor.submit(self._safe_scrape, scraper)
                    futures[future] = name

            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                try:
                    results[name] = future.result()
                    log.info(f"✓ {name} completed: {len(results[name])} records")
                except Exception as e:
                    log.error(f"✗ {name} failed: {e}")
                    continue

        return results

    def _safe_scrape(self, scraper):
        """run scraper with error handling"""
        try:
            return scraper.scrape()
        except Exception as e:
            scraper.log_error(e)
            return []
```

**key features:**
- runs all scrapers in parallel (threadpool)
- graceful failure handling (one scraper fails, others continue)
- checkpoint integration
- structured logging

### 2. plugin-based scraper system (scrapers/base_scraper.py)

abstract base class all scrapers inherit from:

```python
class BaseScraper(ABC):
    """base class for all scrapers"""

    def __init__(self, config):
        self.name = self.__class__.__name__
        self.config = config
        self.http = HTTPClient(
            retry_count=config.get('retries', 3),
            rate_limit=config.get('rate_limit', 2.0)
        )
        self.cache = Cache(enabled=config.get('cache', True))
        self.logger = setup_logger(self.name)

    @abstractmethod
    def scrape(self) -> List[Dict]:
        """main scraping logic - must be implemented"""
        pass

    @abstractmethod
    def parse_article(self, html: str) -> Dict:
        """parse single article/page - must be implemented"""
        pass

    def is_enabled(self) -> bool:
        """check if scraper is enabled in config"""
        return self.config.get('enabled', True)

    def get_priority(self) -> int:
        """get scraper priority (1=highest)"""
        return self.config.get('priority', 99)

    def log_error(self, error: Exception, context: Dict = None):
        """log error to source-specific error file"""
        error_file = f"data/errors/{self.name}_errors.log"
        with open(error_file, 'a') as f:
            f.write(f"{datetime.now()} | {error} | {context}\n")

    def save_raw_data(self, data: List[Dict]):
        """save raw scraper output"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/raw/{self.name}_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
```

**example implementation (scrapers/news/techcabal.py):**

```python
class TechCabalScraper(BaseScraper):
    """scrapes techcabal startup articles"""

    def __init__(self, config):
        super().__init__(config)
        self.base_url = 'https://techcabal.com/category/startups/'
        self.extractor = CompanyExtractor()

    def scrape(self) -> List[Dict]:
        """scrape multiple pages of articles"""
        companies = []

        for page in range(1, self.config.get('max_pages', 5) + 1):
            url = f"{self.base_url}page/{page}/"

            try:
                html = self.http.get(url)
                articles = self._get_article_list(html)

                for article_url in articles:
                    article_html = self.http.get(article_url)
                    data = self.parse_article(article_html)

                    if data:
                        companies.append(data)
                        self.logger.info(f"extracted: {data['name']}")

            except Exception as e:
                self.log_error(e, {'url': url, 'page': page})
                continue

        self.save_raw_data(companies)
        return companies

    def parse_article(self, html: str) -> Dict:
        """extract company data from single article"""
        soup = BeautifulSoup(html, 'html.parser')

        # extract fields using extractor classes
        company_data = {
            'name': self.extractor.extract_company_name(soup),
            'sector': self.extractor.extract_sector(soup),
            'description': self.extractor.extract_description(soup),
            'funding': FundingExtractor().extract(soup),
            'metrics': MetricsExtractor().extract(soup),
            'founders': FounderExtractor().extract(soup),
            'source': 'techcabal',
            'source_url': soup.find('link', rel='canonical')['href'],
            'scraped_at': datetime.now().isoformat()
        }

        return company_data

    def _get_article_list(self, html: str) -> List[str]:
        """get article urls from listing page"""
        soup = BeautifulSoup(html, 'html.parser')
        articles = soup.find_all('article')

        urls = []
        for article in articles:
            link = article.find('a', href=True)
            if link:
                urls.append(link['href'])

        return urls
```

### 3. scraper registry (scrapers/registry.py)

auto-discovers and registers all scrapers:

```python
class ScraperRegistry:
    """auto-discover and register scrapers"""

    def __init__(self, config_path='config/scrapers.yaml'):
        self.config = load_yaml(config_path)
        self.scrapers = {}
        self._discover_scrapers()

    def _discover_scrapers(self):
        """automatically find all scraper classes"""
        scraper_dirs = ['news', 'databases', 'regulatory', 'direct', 'metrics']

        for dir_name in scraper_dirs:
            module_path = f"scrapers.{dir_name}"
            modules = self._get_modules_in_package(module_path)

            for module in modules:
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, BaseScraper) and
                        obj != BaseScraper):

                        scraper_config = self._get_scraper_config(name)
                        self.scrapers[name] = obj(scraper_config)

    def get_enabled_scrapers(self) -> Dict[str, BaseScraper]:
        """return only enabled scrapers sorted by priority"""
        enabled = {
            name: scraper
            for name, scraper in self.scrapers.items()
            if scraper.is_enabled()
        }

        # sort by priority (tier 1 sources first)
        sorted_scrapers = dict(
            sorted(enabled.items(), key=lambda x: x[1].get_priority())
        )

        return sorted_scrapers
```

### 4. unified data models (core/models.py)

consistent data structures across all scrapers:

```python
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
    sources: List[str] = field(default_factory=list)  # track all sources
    source_urls: Dict[str, str] = field(default_factory=dict)
    verification_status: str = 'unverified'
    data_quality_score: int = 0

    # regulatory
    cac_verified: bool = False
    cbn_licensed: bool = False

    def add_source(self, source_name: str, source_url: str):
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

        # merge founders (union)
        self.founders = list(set(self.founders + other.founders))

        # add sources
        for source in other.sources:
            self.add_source(source, other.source_urls.get(source, ''))

        # keep most specific sector
        if other.sub_sector and not self.sub_sector:
            self.sub_sector = other.sub_sector

        # fill missing fields
        for field in ['website', 'founded_year', 'team_size', 'linkedin_url']:
            if getattr(other, field) and not getattr(self, field):
                setattr(self, field, getattr(other, field))

@dataclass
class FundingRound:
    """unified funding round model"""
    company_name: str  # will be linked to company_id later
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
    update_date: date = field(default_factory=date.today)

    company_id: Optional[int] = None
```

### 5. triangulation engine (core/triangulation.py)

cross-references and merges data from multiple sources:

```python
class Triangulator:
    """cross-reference and verify data from multiple sources"""

    def __init__(self):
        self.deduplicator = Deduplicator()
        self.normalizer = NameNormalizer()

    def process(self, raw_data: Dict[str, List[Dict]]) -> Dict:
        """
        takes raw data from all scrapers
        returns aggregated, deduplicated, verified data
        """
        # step 1: convert raw dicts to unified models
        companies = self._convert_to_models(raw_data)

        # step 2: deduplicate by website + fuzzy name matching
        unique_companies = self._deduplicate_companies(companies)

        # step 3: merge related data (funding, metrics, etc.)
        aggregated = self._aggregate_related_data(unique_companies, raw_data)

        # step 4: calculate quality scores
        self._calculate_quality_scores(aggregated['companies'])

        return aggregated

    def _deduplicate_companies(self, companies: List[Company]) -> List[Company]:
        """merge duplicate companies from different sources"""
        unique = {}

        for company in companies:
            # try to find existing match
            match_key = self._find_match(company, unique)

            if match_key:
                # merge with existing
                unique[match_key].merge_with(company)
            else:
                # add as new
                key = self._get_company_key(company)
                unique[key] = company

        return list(unique.values())

    def _find_match(self, company: Company, existing: Dict) -> Optional[str]:
        """find matching company in existing dict"""
        # exact website match
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
                return key

        return None

    def _get_company_key(self, company: Company) -> str:
        """generate unique key for company"""
        if company.website:
            return self.normalizer.normalize_url(company.website)
        else:
            return self.normalizer.normalize_name(company.name)

    def _calculate_quality_scores(self, companies: List[Company]):
        """calculate data quality score for each company"""
        for company in companies:
            score = 50  # base score

            # completeness
            if company.website: score += 10
            if company.long_description: score += 5
            if company.founded_year: score += 5
            if company.team_size: score += 5
            if company.founders: score += 5

            # verification
            source_count = len(company.sources)
            if source_count >= 3: score += 20
            elif source_count == 2: score += 10
            elif source_count == 1: score += 5

            company.data_quality_score = min(score, 100)
```

### 6. configuration system (config/scrapers.yaml)

yaml-based config for easy maintenance:

```yaml
# config/scrapers.yaml

global_settings:
  max_workers: 5  # parallel scraper threads
  default_rate_limit: 2.0  # seconds between requests
  default_retries: 3
  cache_enabled: true
  cache_ttl: 3600  # 1 hour

# tier 1 scrapers (high priority)
news_scrapers:
  techcabal:
    enabled: true
    priority: 1
    max_pages: 10
    rate_limit: 2.0
    reliability_score: 90

  techpoint:
    enabled: true
    priority: 1
    max_pages: 10
    rate_limit: 2.0
    reliability_score: 90

  the_big_deal:
    enabled: true
    priority: 1
    max_pages: 5
    rate_limit: 3.0
    reliability_score: 95

  disrupt_africa:
    enabled: true
    priority: 2
    max_pages: 10
    rate_limit: 2.0
    reliability_score: 85

  nairametrics:
    enabled: true
    priority: 2
    max_pages: 10
    rate_limit: 2.0
    reliability_score: 80

# structured data sources
database_scrapers:
  crunchbase:
    enabled: true
    priority: 1
    use_api: true
    api_key: env:CRUNCHBASE_API_KEY
    rate_limit: 5.0
    reliability_score: 95

  vc_blogs:
    enabled: true
    priority: 2
    rate_limit: 3.0
    vcs:
      - ventures_platform
      - tlcom_capital
      - future_africa
    reliability_score: 95

# regulatory sources
regulatory_scrapers:
  cbn_licenses:
    enabled: true
    priority: 1
    rate_limit: 5.0
    reliability_score: 100

  cac_registry:
    enabled: false  # requires search, implement later
    priority: 2
    reliability_score: 100

# direct company sources
direct_scrapers:
  company_websites:
    enabled: true
    priority: 1
    rate_limit: 1.0
    pages_to_scrape:
      - /about
      - /team
      - /contact
    reliability_score: 90

  linkedin_pages:
    enabled: false  # needs auth, implement carefully
    priority: 2
    rate_limit: 10.0
    reliability_score: 85

# metrics sources
metrics_scrapers:
  app_stores:
    enabled: true
    priority: 3
    rate_limit: 2.0
    reliability_score: 85
```

## usage

### simple one-command execution

```bash
# run everything
python main.py

# resume from last checkpoint
python main.py --resume

# dry run (no database writes)
python main.py --dry-run

# run specific scrapers only
python main.py --scrapers techcabal,techpoint,the_big_deal

# test with limited data
python main.py --limit 10
```

### main.py implementation

```python
#!/usr/bin/env python3
"""
lemina scraper - master entry point
"""

import argparse
from core.orchestrator import Orchestrator
from core.logging_config import setup_logging

def main():
    parser = argparse.ArgumentParser(description='lemina startup data scraper')
    parser.add_argument('--resume', action='store_true', help='resume from checkpoint')
    parser.add_argument('--dry-run', action='store_true', help='run without db writes')
    parser.add_argument('--scrapers', type=str, help='comma-separated scraper names')
    parser.add_argument('--limit', type=int, help='limit companies to scrape')
    parser.add_argument('--config', type=str, default='config/scrapers.yaml')

    args = parser.parse_args()

    # setup logging
    setup_logging()

    # create orchestrator
    orchestrator = Orchestrator(
        config_path=args.config,
        dry_run=args.dry_run,
        limit=args.limit,
        enabled_scrapers=args.scrapers.split(',') if args.scrapers else None
    )

    # run pipeline
    print("=" * 60)
    print("LEMINA STARTUP DATA SCRAPER")
    print("=" * 60)
    print()

    orchestrator.run(resume=args.resume)

    print()
    print("=" * 60)
    print("✓ SCRAPING COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    main()
```

## key advantages of this architecture

1. **scalability** - add new scraper by creating one file in scrapers/, auto-discovered
2. **maintainability** - each scraper is isolated, changes don't affect others
3. **single command** - `python main.py` runs everything
4. **fault tolerance** - one scraper failure doesn't stop others
5. **configurable** - enable/disable scrapers via yaml, no code changes
6. **resumable** - checkpoint system for long-running scrapes
7. **observable** - structured logs, metrics, progress tracking
8. **testable** - dry-run mode, limit flag, unit tests
9. **extensible** - plugin system makes adding features easy

## implementation priority

**mvp: core + tier 1 scrapers**
- orchestrator, base scraper, models, registry
- http client with retry logic
- techcabal, techpoint scrapers
- basic extractors (company name, sector, funding)
- simple triangulation (deduplication by name)
- database insertion (companies table only)

**v1: full triangulation + more scrapers**
- the big deal scraper
- fuzzy matching deduplication
- quality score calculation
- all database tables (funding_rounds, metrics, etc.)
- progress tracking and checkpoints

**v2: regulatory + advanced features**
- cbn licenses scraper
- company website scraper
- vc blogs scraper
- caching layer
- comprehensive error handling

**v3: polish + optimization**
- crunchbase api integration
- parallel scraping optimization
- monitoring dashboard
- comprehensive testing

## next steps

ready to start implementation. which component should we build first?

1. core infrastructure (orchestrator, base scraper, models)
2. first scraper (techcabal or techpoint)
3. extractors (company, funding parsers)
4. database layer

or build end-to-end mvp in one go?
