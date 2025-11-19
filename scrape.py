#!/usr/bin/env python3
"""
Nigerian Startup Scraper
Collects company data from TechCabal, Techpoint, and other sources
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urlparse

class NigerianStartupScraper:
    def __init__(self):
        self.companies = []
        self.seen_names = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def clean_company_name(self, text):
        """Extract company name from article title"""
        # Remove common patterns
        text = re.sub(r'\s+raises?\s+.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+secures?\s+.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+launches?\s+.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+announces?\s+.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r':.*', '', text)
        text = text.strip()
        return text
    
    def extract_sector(self, text):
        """Determine sector from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['payment', 'fintech', 'bank', 'wallet', 'transfer', 'lending', 'credit']):
            return 'Fintech'
        elif any(word in text_lower for word in ['ecommerce', 'e-commerce', 'marketplace', 'retail', 'shop']):
            return 'E-commerce'
        elif any(word in text_lower for word in ['health', 'medical', 'hospital', 'clinic', 'pharma', 'telemedicine']):
            return 'Healthtech'
        elif any(word in text_lower for word in ['education', 'learning', 'school', 'tutor', 'edtech']):
            return 'Edtech'
        elif any(word in text_lower for word in ['farm', 'agric', 'crop', 'agritech']):
            return 'Agritech'
        elif any(word in text_lower for word in ['logistics', 'delivery', 'shipping', 'transport']):
            return 'Logistics'
        else:
            return 'Other'
    
    def scrape_techcabal(self):
        """Scrape TechCabal startup articles"""
        print("🔍 Scraping TechCabal...")
        
        try:
            url = 'https://techcabal.com/category/startups/'
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('article', limit=30)
            
            for article in articles:
                try:
                    title_elem = article.find('h2')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text().strip()
                    link = title_elem.find('a')['href'] if title_elem.find('a') else None
                    
                    company_name = self.clean_company_name(title)
                    
                    if len(company_name) < 3 or company_name.lower() in self.seen_names:
                        continue
                    
                    excerpt = ''
                    excerpt_elem = article.find('div', class_='entry-excerpt')
                    if excerpt_elem:
                        excerpt = excerpt_elem.get_text().strip()
                    
                    sector = self.extract_sector(title + ' ' + excerpt)
                    
                    self.companies.append({
                        'name': company_name,
                        'sector': sector,
                        'description': excerpt[:200] if excerpt else f'{company_name} - Nigerian startup',
                        'source_url': link,
                        'source': 'TechCabal'
                    })
                    
                    self.seen_names.add(company_name.lower())
                    print(f"  ✓ Found: {company_name} ({sector})")
                    
                except Exception as e:
                    continue
            
            print(f"✅ TechCabal: Found {len([c for c in self.companies if c['source'] == 'TechCabal'])} companies\n")
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error scraping TechCabal: {e}\n")
    
    def scrape_techpoint(self):
        """Scrape Techpoint Africa"""
        print("🔍 Scraping Techpoint Africa...")
        
        try:
            url = 'https://techpoint.africa/category/startups/'
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('article', limit=30)
            
            for article in articles:
                try:
                    title_elem = article.find('h2') or article.find('h3')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text().strip()
                    link_elem = title_elem.find('a')
                    link = link_elem['href'] if link_elem else None
                    
                    company_name = self.clean_company_name(title)
                    
                    if len(company_name) < 3 or company_name.lower() in self.seen_names:
                        continue
                    
                    excerpt = ''
                    excerpt_elem = article.find('div', class_='entry-content') or article.find('p')
                    if excerpt_elem:
                        excerpt = excerpt_elem.get_text().strip()
                    
                    sector = self.extract_sector(title + ' ' + excerpt)
                    
                    self.companies.append({
                        'name': company_name,
                        'sector': sector,
                        'description': excerpt[:200] if excerpt else f'{company_name} - Nigerian startup',
                        'source_url': link,
                        'source': 'Techpoint'
                    })
                    
                    self.seen_names.add(company_name.lower())
                    print(f"  ✓ Found: {company_name} ({sector})")
                    
                except Exception as e:
                    continue
            
            print(f"✅ Techpoint: Found {len([c for c in self.companies if c['source'] == 'Techpoint'])} companies\n")
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error scraping Techpoint: {e}\n")
    
    def add_known_companies(self):
        """Add well-known Nigerian startups to ensure coverage"""
        print("📋 Adding known Nigerian startups...")
        
        known_companies = [
            {'name': 'Flutterwave', 'sector': 'Fintech', 'website': 'https://flutterwave.com', 'description': 'Payment infrastructure for Africa'},
            {'name': 'Paystack', 'sector': 'Fintech', 'website': 'https://paystack.com', 'description': 'Modern online payments for Africa'},
            {'name': 'Kuda Bank', 'sector': 'Fintech', 'website': 'https://kuda.com', 'description': 'Digital bank for Africans'},
            {'name': 'OPay', 'sector': 'Fintech', 'website': 'https://opayweb.com', 'description': 'Mobile money and payments'},
            {'name': 'Moniepoint', 'sector': 'Fintech', 'website': 'https://moniepoint.com', 'description': 'All-in-one banking for businesses'},
            {'name': 'Piggyvest', 'sector': 'Fintech', 'website': 'https://piggyvest.com', 'description': 'Save and invest with ease'},
            {'name': 'Carbon', 'sector': 'Fintech', 'website': 'https://getcarbon.co', 'description': 'Digital financial services'},
            {'name': 'Interswitch', 'sector': 'Fintech', 'website': 'https://interswitch.com', 'description': 'Payment processing and switching'},
            {'name': 'Cowrywise', 'sector': 'Fintech', 'website': 'https://cowrywise.com', 'description': 'Automated wealth management'},
            {'name': 'Renmoney', 'sector': 'Fintech', 'website': 'https://renmoney.com', 'description': 'Digital lending platform'},
            {'name': 'Jumia', 'sector': 'E-commerce', 'website': 'https://jumia.com.ng', 'description': 'Online marketplace'},
            {'name': 'Konga', 'sector': 'E-commerce', 'website': 'https://konga.com', 'description': 'E-commerce and logistics'},
            {'name': 'Jiji', 'sector': 'E-commerce', 'website': 'https://jiji.ng', 'description': 'Classifieds marketplace'},
            {'name': 'Helium Health', 'sector': 'Healthtech', 'website': 'https://heliumhealth.com', 'description': 'Healthcare technology platform'},
            {'name': '54gene', 'sector': 'Healthtech', 'website': 'https://54gene.com', 'description': 'Health data science company'},
            {'name': 'LifeBank', 'sector': 'Healthtech', 'website': 'https://lifebank.ng', 'description': 'Medical supplies delivery'},
            {'name': 'uLesson', 'sector': 'Edtech', 'website': 'https://ulesson.com', 'description': 'Online learning platform'},
            {'name': 'Gradely', 'sector': 'Edtech', 'website': 'https://gradely.ng', 'description': 'AI-powered learning platform'},
            {'name': 'Farmcrowdy', 'sector': 'Agritech', 'website': 'https://farmcrowdy.com', 'description': 'Digital agriculture platform'},
            {'name': 'ThriveAgric', 'sector': 'Agritech', 'website': 'https://thriveagric.com', 'description': 'Agricultural financing'},
        ]
        
        for company in known_companies:
            if company['name'].lower() not in self.seen_names:
                self.companies.append({
                    'name': company['name'],
                    'sector': company['sector'],
                    'website': company.get('website', ''),
                    'description': company['description'],
                    'source': 'Manual',
                    'source_url': None
                })
                self.seen_names.add(company['name'].lower())
                print(f"  ✓ Added: {company['name']}")
        
        print(f"✅ Added {len(known_companies)} known companies\n")
    
    def save_results(self):
        """Save scraped companies to JSON"""
        output_file = 'data/scraped_companies.json'
        
        import os
        os.makedirs('data', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.companies, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(self.companies)} companies to {output_file}")
    
    def run(self):
        """Run the scraper"""
        print("=" * 60)
        print("NIGERIAN STARTUP SCRAPER")
        print("=" * 60 + "\n")
        
        self.add_known_companies()
        self.scrape_techcabal()
        self.scrape_techpoint()
        
        print("\n" + "=" * 60)
        print(f"TOTAL COMPANIES FOUND: {len(self.companies)}")
        print("=" * 60)
        
        # Show sector breakdown
        sectors = {}
        for company in self.companies:
            sector = company['sector']
            sectors[sector] = sectors.get(sector, 0) + 1
        
        print("\nSECTOR BREAKDOWN:")
        for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
            print(f"  {sector}: {count} companies")
        
        self.save_results()
        print("\n✅ Scraping complete!")

if __name__ == '__main__':
    scraper = NigerianStartupScraper()
    scraper.run()
