# lemina scraper

automated data collection system for nigerian startup intelligence.

## what we're building

a market intelligence platform that collects, verifies, and maintains data on 100+ nigerian tech companies from multiple sources. the system automatically discovers companies, extracts funding rounds, tracks traction metrics, and monitors regulatory licenses.

### the goal: 5-phase pipeline

every data point flows through 5 distinct phases:

1. **collection** - scrape raw data from news sites, databases, regulatory sources
2. **cleaning & processing** - parse html, extract entities, normalize formats
3. **verification & interpretation** - cross-reference multiple sources, calculate quality scores
4. **presentation** - format for console, csv, json, dashboards
5. **storage** - persist to supabase postgresql with full referential integrity

this ensures high data quality through triangulation: companies verified by 3+ sources are marked "verified", 2 sources as "cross_referenced", single source as "self_reported".

---

## current status (v1 foundation)

### what's built and working

✅ **core infrastructure**
- orchestrator that coordinates entire pipeline
- plugin-based scraper system (auto-discovery)
- unified data models (company, fundinground, companyupdate)
- triangulation engine for deduplication
- supabase database layer with upsert logic
- parallel scraping (threadpool)
- comprehensive error handling

✅ **data extraction**
- intelligent company name extraction (not headlines!)
- sector classification via keyword matching
- founder extraction with regex patterns
- funding round detection and parsing
- amount parsing: "$5m" → 5000000
- date parsing with multiple formats
- description extraction from articles

✅ **quality & verification**
- fuzzy name matching for deduplication (>90% similarity)
- website-based deduplication (primary method)
- data quality scoring (0-100)
- verification status calculation based on source count
- source tracking (which data came from which article)

✅ **database operations**
- companies table: upsert by website or name
- funding_rounds table: linked via company_id
- company_updates table: news articles tracked
- handles reruns gracefully (updates existing records)
- proper foreign key relationships

### current results

**60 companies in database**
- 40 from automated scraping (techcabal)
- 20 from legacy manual seed list
- sectors: fintech (19), healthtech (9), saas (4), edtech, agritech
- average quality score: 67.4/100
- 34 company updates tracked
- 21 funding rounds extracted

**sample companies:**
accrue, mydébboapp, eyeguide, m-kopa, oko, koolboks, clarrio.ai, watu credit, flutterwave

---

## quick start

```bash
# install dependencies
cd scripts
pip install -r requirements.txt

# setup environment
cp .env.local.example .env.local
# add your supabase credentials:
#   NEXT_PUBLIC_SUPABASE_URL=your_url
#   SUPABASE_SERVICE_ROLE_KEY=your_key

# run full pipeline
python main.py
```

## usage

```bash
# full pipeline (all 5 phases)
python main.py

# dry run (skip storage phase)
python main.py --dry-run

# custom config
python main.py --config config/scrapers.yaml
```

## configuration

edit `config/scrapers.yaml` to control scraper behavior:

```yaml
global_settings:
  max_workers: 3          # parallel scrapers
  default_rate_limit: 2.0 # seconds between requests

news_scrapers:
  techcabal:
    enabled: true
    max_pages: 5          # scrape 5 pages of articles
    rate_limit: 1.0
    reliability_score: 90

  techpoint:
    enabled: false        # disabled (needs html parsing fix)
```

---

## architecture overview

### directory structure

```
scripts/
├── main.py                      # entry point
├── config/scrapers.yaml         # scraper configs
│
├── core/                        # pipeline orchestration
│   ├── orchestrator.py          # runs all 5 phases
│   ├── models.py                # company, fundinround, update models
│   ├── triangulation.py         # phase 3: verification
│   └── database.py              # phase 5: storage
│
├── scrapers/                    # phase 1: collection
│   ├── base_scraper.py          # abstract base class
│   └── news/
│       ├── techcabal.py         # ✅ working
│       ├── techpoint.py         # ⚠ needs html fix
│       └── (add more here)
│
├── extractors/                  # phase 2: cleaning/processing
│   ├── company_extractor.py     # extract company data
│   ├── funding_extractor.py     # extract funding rounds
│   └── parsers/
│       ├── amount_parser.py     # parse "$5m series a"
│       └── date_parser.py       # parse "january 2024"
│
└── utils/
    ├── http_client.py           # retry logic, rate limiting
    └── deduplicator.py          # fuzzy name matching
```

### current pipeline flow

```
orchestrator.run()
  │
  ├─→ phase 1: collection (scrapers run in parallel)
  │   └─→ returns: {'techcabal': [...article data...]}
  │
  ├─→ phase 2: cleaning/processing (currently embedded in scrapers)
  │   └─→ extractors parse html → structured dicts
  │
  ├─→ phase 3: verification (triangulation.py)
  │   └─→ deduplicate, merge sources, calculate quality scores
  │
  ├─→ phase 4: presentation (summary only)
  │   └─→ console summary report
  │
  └─→ phase 5: storage (database.py)
      └─→ upsert companies, insert funding_rounds, updates
```

### adding a new scraper

1. create `scrapers/news/newsource.py`:

```python
from scrapers.base_scraper import BaseScraper
from extractors.company_extractor import CompanyExtractor

class NewSourceScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.base_url = 'https://newsource.com/startups'
        self.extractor = CompanyExtractor()

    def scrape(self):
        """main scraping logic"""
        results = []

        for page in range(1, self.config.get('max_pages', 3) + 1):
            html = self.http.get(f"{self.base_url}/page/{page}")
            articles = self._extract_articles(html)

            for article_url in articles:
                article_html = self.http.get(article_url)
                company_data = self.extractor.extract(article_html, article_url)

                if company_data:
                    results.append(company_data)

        return results
```

2. add to `config/scrapers.yaml`:

```yaml
news_scrapers:
  newsource:
    enabled: true
    max_pages: 5
    rate_limit: 2.0
    reliability_score: 85
```

3. run `python main.py` - orchestrator auto-discovers it!

---

## logical next steps

### phase 1: complete core scrapers (week 1-2)

**goal:** scale from 60 to 150+ companies with cross-referenced data

1. **fix techpoint scraper** (`scrapers/news/techpoint.py`)
   - update html selectors for current site structure
   - test with `python main.py --dry-run`
   - enable in config: `techpoint.enabled = true`

2. **add the big deal scraper** (create `scrapers/news/the_big_deal.py`)
   - focused on funding announcements
   - high reliability score (95)
   - prioritize extracting funding_rounds

3. **add disrupt africa scraper** (create `scrapers/news/disrupt_africa.py`)
   - excellent funding coverage
   - reliability score: 85

4. **verify triangulation works**
   - run with 3+ sources enabled
   - confirm companies get "verified" status
   - check deduplication merges correctly

### phase 2: separate processing from collection (week 2-3)

**goal:** make phase 2 (cleaning/processing) explicit

currently, scrapers call extractors internally. separate this:

1. **create `core/processor.py`**
   - receives raw html/json from scrapers
   - coordinates all extractors
   - returns structured dicts

2. **refactor scrapers to return raw data**
   - scrapers should only fetch, not parse
   - move extraction logic to processor

3. **update orchestrator**
   ```python
   # phase 1: collection
   raw_data = self._run_scrapers()  # returns raw html

   # phase 2: cleaning (new explicit phase)
   processed_data = self.processor.process(raw_data)  # parse html
   ```

### phase 3: expand presentation outputs (week 3-4)

**goal:** make phase 4 (presentation) a proper formatting layer

currently only console summary. add multiple outputs:

1. **create `core/presenter.py`**
   ```python
   class Presenter:
       def generate_console_summary(self, data)
       def export_csv(self, data, path)
       def export_json(self, data, path)
       def generate_quality_dashboard(self, data)
   ```

2. **add csv export** (`exports/csv_exporter.py`)
   - companies.csv for spreadsheet analysis
   - funding_rounds.csv for investor tracking

3. **add json export** (`exports/json_exporter.py`)
   - api-ready format for frontend
   - include metadata (export timestamp, data quality avg)

4. **create quality dashboard** (`reports/quality_dashboard.py`)
   - html dashboard with charts
   - verification status distribution
   - sector breakdown
   - low-quality companies flagged for review

### phase 4: add regulatory scrapers (week 4-5)

**goal:** verify company legitimacy via official sources

1. **cbn licensed entities** (`scrapers/regulatory/cbn_licenses.py`)
   - scrape central bank of nigeria licensed payment providers
   - update `cbn_licensed` flag in companies table
   - insert to regulatory_info table

2. **sec registered advisors** (`scrapers/regulatory/sec_registry.py`)
   - securities and exchange commission registry
   - update `sec_registered` flag

3. **update verification logic**
   - regulatory sources count as "verified" source
   - boost quality score for regulatory-verified companies

### phase 5: add direct company sources (week 5-6)

**goal:** enrich data with first-party information

1. **company website scraper** (`scrapers/direct/company_websites.py`)
   - scrape /about, /team, /contact pages
   - extract team_size, founders, product details
   - discover linkedin_url, twitter_url from footer

2. **enhance deduplication**
   - use discovered websites to link articles to companies
   - improve verification status calculation

### phase 6: scale to 100+ companies (week 6-7)

**goal:** reach target dataset size with quality data

1. **increase scraping depth**
   - set `max_pages: 10` for all scrapers
   - run full historical scrape

2. **add manual seed list** (optional)
   - create `data/seed_companies.csv` with known startups
   - scrape their websites directly
   - search news sources for mentions

3. **run full verification pass**
   - all companies cross-referenced across sources
   - quality scores recalculated
   - low-quality records flagged for manual review

---

## data output locations

```
data/
├── raw/                         # phase 1 output
│   ├── techcabal_20251117.json
│   └── techpoint_20251117.json
│
├── processed/                   # phase 2 output (future)
│   └── aggregated_20251117.json
│
├── exports/                     # phase 4 output (future)
│   ├── companies.csv
│   ├── funding_rounds.csv
│   ├── aggregated.json
│   └── quality_dashboard.html
│
└── errors/
    └── techcabal_errors.log
```

**database** (phase 5 output):
- companies (60 records)
- funding_rounds (21 records)
- company_updates (34 records)
- regulatory_info (pending)
- metrics (pending)

---

## key technical decisions

### why triangulation?

nigerian startup data is fragmented across multiple sources with varying quality. triangulation ensures:
- high confidence in verified data (3+ sources agree)
- detection of conflicts (different funding amounts reported)
- completeness (merge details from multiple articles)

### why upsert pattern?

supports rerunning scraper without duplicates:
- check if company exists by website (primary key)
- if exists: update fields with newer/better data
- if new: insert with `created_by = 'scraper'`

### why plugin-based scrapers?

easy to add new sources without touching core code:
- drop new scraper in `scrapers/news/`
- add config entry
- orchestrator auto-discovers and runs it

---

## see also

- `ARCHITECTURE.md` - detailed system design and component specs
- `DATA_SOURCES.md` - inventory of 29 potential data sources
- `RESULTS.md` - current scraping results and statistics
- `CLAUDE.md` - development guidelines for claude code

---

## troubleshooting

**no data scraped:**
- check internet connection
- verify site structure hasn't changed (inspect html)
- check rate limits in config

**database errors:**
- verify supabase credentials in `.env.local`
- ensure service role key (not anon key) is used
- check table schemas match models

**low quality scores:**
- enable more scrapers for cross-referencing
- improve extraction patterns in extractors/
- add website discovery for better deduplication
