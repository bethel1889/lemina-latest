"""
techcabal scraper
"""

from typing import List, Dict
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from extractors.company_extractor import CompanyExtractor
from extractors.funding_extractor import FundingExtractor


class TechCabalScraper(BaseScraper):
    """scrape startup articles from techcabal"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = 'https://techcabal.com/category/startups/'
        self.company_extractor = CompanyExtractor()
        self.funding_extractor = FundingExtractor()

    def scrape(self) -> List[Dict]:
        """scrape techcabal startup articles"""
        self.logger.info("starting techcabal scrape...")

        max_pages = self.config.get('max_pages', 5)

        for page in range(1, max_pages + 1):
            url = f"{self.base_url}page/{page}/" if page > 1 else self.base_url

            try:
                self.logger.info(f"scraping page {page}/{max_pages}: {url}")
                html = self.http.get(url)

                if not html:
                    self.logger.warning(f"failed to fetch page {page}")
                    continue

                # get article urls
                article_urls = self._get_article_urls(html)
                self.logger.info(f"found {len(article_urls)} articles on page {page}")

                # scrape each article
                for article_url in article_urls:
                    try:
                        data = self._scrape_article(article_url)
                        if data:
                            self.add_result(data)
                            self.logger.info(f"  ✓ extracted: {data['name']}")
                    except Exception as e:
                        self.log_error(e, {'url': article_url})
                        continue

            except Exception as e:
                self.log_error(e, {'url': url, 'page': page})
                continue

        self.save_raw_data(self.results)
        self.logger.info(f"✓ techcabal complete: {len(self.results)} companies")

        return self.results

    def _get_article_urls(self, html: str) -> List[str]:
        """extract article urls from listing page"""
        soup = BeautifulSoup(html, 'html.parser')
        urls = []

        # find all h2 tags with links
        h2_tags = soup.find_all('h2')

        for h2 in h2_tags:
            link = h2.find('a', href=True)
            if link and link['href']:
                # only include article urls (not category pages)
                href = link['href']
                if '/category/' not in href and 'techcabal.com/20' in href:
                    urls.append(href)

        return urls

    def _scrape_article(self, url: str) -> Dict:
        """scrape single article"""
        html = self.http.get(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # extract title
        title_elem = soup.find('h1', class_=lambda x: x and 'entry-title' in x) or soup.find('h1')
        title = title_elem.get_text().strip() if title_elem else ''

        if not title:
            return None

        # extract company name
        company_name = self.company_extractor.extract_company_name(soup, title)
        if not company_name or len(company_name) < 2:
            return None

        # get full text for analysis
        full_text = soup.get_text()

        # check if nigerian company
        if not self.company_extractor.is_nigerian_company(full_text, title):
            self.logger.debug(f"  ⊘ skipped non-nigerian: {company_name}")
            return None

        # extract company data
        data = {
            'name': company_name,
            'sector': self.company_extractor.extract_sector(full_text),
            'short_description': self.company_extractor.extract_description(soup),
            'website': self.company_extractor.extract_website(soup, full_text),
            'founders': self.company_extractor.extract_founders(full_text),
            'source': 'techcabal',
            'source_url': url,
        }

        # try to extract funding info
        funding_data = self.funding_extractor.extract(soup, company_name)
        if funding_data:
            data['funding'] = funding_data

        return data
