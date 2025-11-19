#!/usr/bin/env python3
"""
test company name extraction
"""

import requests
from bs4 import BeautifulSoup
from extractors.company_extractor import CompanyExtractor

# test urls with real companies
test_urls = [
    'https://techcabal.com/2025/11/06/accrue-is-building-a-human-network-for-stablecoin-payments-across-africa/',
    'https://techcabal.com/2025/10/27/when-the-doctor-wont-listen-to-you-mydebboapp-bets-it-will/',
    'https://techcabal.com/2025/10/07/m-kopa-turns-first-ever-profit-revenue-surges-66-416/',
]

extractor = CompanyExtractor()
headers = {'User-Agent': 'Mozilla/5.0'}

print("testing improved company name extraction:\n")
print("=" * 70)

for url in test_urls:
    try:
        print(f"\nurl: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # get title
        title = soup.find('h1').get_text().strip() if soup.find('h1') else ''
        print(f"title: {title}")

        # extract company name
        company_name = extractor.extract_company_name(soup, title)
        print(f"✓ extracted company: {company_name}")

        # get first paragraph for context
        article_body = soup.find('article') or soup.find('div', class_='entry-content')
        if article_body:
            first_para = article_body.find('p')
            if first_para:
                para_text = first_para.get_text().strip()[:150]
                print(f"context: {para_text}...")

        print("-" * 70)

    except Exception as e:
        print(f"✗ error: {e}")
        print("-" * 70)

print("\ntest complete!")
