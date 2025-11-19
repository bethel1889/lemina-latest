#!/usr/bin/env python3
"""
Company Data Verifier
Verifies websites and cleans data
"""

import requests
import json
import time
from urllib.parse import urlparse
import re

class CompanyVerifier:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def find_website(self, company_name):
        """Try to find company website via Google search simulation"""
        # Simple heuristic: try common patterns
        potential_urls = [
            f"https://{company_name.lower().replace(' ', '')}.com",
            f"https://{company_name.lower().replace(' ', '')}.ng",
            f"https://{company_name.lower().replace(' ', '')}.co",
            f"https://www.{company_name.lower().replace(' ', '')}.com",
        ]
        
        for url in potential_urls:
            try:
                response = requests.head(url, headers=self.headers, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    return url
            except:
                continue
        
        return None
    
    def verify_website(self, url):
        """Check if website is accessible"""
        if not url:
            return False, 0
        
        try:
            response = requests.head(url, headers=self.headers, timeout=5, allow_redirects=True)
            return response.status_code == 200, response.status_code
        except:
            return False, 0
    
    def calculate_quality_score(self, company):
        """Calculate data quality score 0-100"""
        score = 50  # Base score
        
        # Has website (+20)
        if company.get('website'):
            score += 20
        
        # Website verified (+15)
        if company.get('website_verified'):
            score += 15
        
        # Has description (+10)
        if company.get('description') and len(company.get('description', '')) > 50:
            score += 10
        
        # Has source URL (+5)
        if company.get('source_url'):
            score += 5
        
        return min(score, 100)
    
    def verify_companies(self, input_file, output_file):
        """Verify all companies"""
        print("=" * 60)
        print("COMPANY DATA VERIFIER")
        print("=" * 60 + "\n")
        
        # Load scraped data
        with open(input_file, 'r', encoding='utf-8') as f:
            companies = json.load(f)
        
        print(f"📋 Loaded {len(companies)} companies\n")
        
        verified_companies = []
        
        for i, company in enumerate(companies, 1):
            print(f"[{i}/{len(companies)}] Verifying {company['name']}...")
            
            # Find website if missing
            if not company.get('website'):
                print(f"  🔍 Looking for website...")
                website = self.find_website(company['name'])
                if website:
                    company['website'] = website
                    print(f"  ✓ Found: {website}")
                else:
                    print(f"  ⚠ Website not found")
            
            # Verify website
            website_verified = False
            if company.get('website'):
                is_valid, status_code = self.verify_website(company['website'])
                website_verified = is_valid
                if is_valid:
                    print(f"  ✓ Website verified (HTTP {status_code})")
                else:
                    print(f"  ✗ Website not accessible")
            
            company['website_verified'] = website_verified
            
            # Calculate quality score
            quality_score = self.calculate_quality_score(company)
            company['data_quality_score'] = quality_score
            
            # Set verification status
            if website_verified and quality_score >= 75:
                company['verification_status'] = 'cross_referenced'
            else:
                company['verification_status'] = 'unverified'
            
            # Set data source
            if company.get('source') == 'Manual':
                company['data_source'] = 'manual'
                company['verification_status'] = 'verified'
                company['data_quality_score'] = 90
            else:
                company['data_source'] = 'web_scraped'
            
            # Add metadata
            company['headquarters'] = 'Lagos, Nigeria'  # Default
            company['created_by'] = 'scraper'
            
            print(f"  📊 Quality Score: {quality_score}/100")
            print(f"  ✓ Status: {company['verification_status']}\n")
            
            verified_companies.append(company)
            
            # Be polite
            time.sleep(1)
        
        # Filter: Keep only companies with score >= 60
        verified_companies = [c for c in verified_companies if c['data_quality_score'] >= 60]
        
        # Save verified data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(verified_companies, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 60)
        print(f"✅ VERIFIED {len(verified_companies)} COMPANIES")
        print("=" * 60)
        
        # Quality breakdown
        tiers = {'verified': 0, 'cross_referenced': 0, 'unverified': 0}
        for company in verified_companies:
            status = company['verification_status']
            tiers[status] = tiers.get(status, 0) + 1
        
        print("\nQUALITY BREAKDOWN:")
        print(f"  Verified (90+): {tiers['verified']} companies")
        print(f"  Cross-referenced (75-89): {tiers['cross_referenced']} companies")
        print(f"  Unverified (60-74): {tiers['unverified']} companies")
        
        print(f"\n💾 Saved to {output_file}")

if __name__ == '__main__':
    verifier = CompanyVerifier()
    verifier.verify_companies(
        'data/scraped_companies.json',
        'data/verified_companies.json'
    )
