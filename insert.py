#!/usr/bin/env python3
"""
Supabase Bulk Inserter
Inserts verified companies into Supabase
"""

import json
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

class SupabaseInserter:
    def __init__(self):
        url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not url or not key:
            raise ValueError("Missing Supabase credentials in .env.local")
        
        self.supabase: Client = create_client(url, key)
        print("✅ Connected to Supabase\n")
    
    def insert_companies(self, input_file):
        """Insert companies into Supabase"""
        print("=" * 60)
        print("SUPABASE BULK INSERTER")
        print("=" * 60 + "\n")
        
        # Load verified data
        with open(input_file, 'r', encoding='utf-8') as f:
            companies = json.load(f)
        
        print(f"📋 Loaded {len(companies)} companies\n")
        
        inserted = 0
        failed = 0
        
        for i, company in enumerate(companies, 1):
            try:
                # Prepare data for Supabase
                data = {
                    'name': company['name'],
                    'website': company.get('website', ''),
                    'sector': company['sector'],
                    'sub_sector': company.get('sub_sector', company['sector']),
                    'short_description': company['description'][:500],  # Limit length
                    'headquarters': company.get('headquarters', 'Lagos, Nigeria'),
                    'verification_status': company['verification_status'],
                    'data_quality_score': company['data_quality_score'],
                    'data_source': company['data_source'],
                    'created_by': company.get('created_by', 'scraper')
                }
                
                # Insert to Supabase
                result = self.supabase.table('companies').insert(data).execute()
                
                print(f"[{i}/{len(companies)}] ✓ Inserted: {company['name']}")
                inserted += 1
                
            except Exception as e:
                print(f"[{i}/{len(companies)}] ✗ Failed: {company['name']} - {str(e)}")
                failed += 1
                continue
        
        print("\n" + "=" * 60)
        print(f"✅ INSERTED: {inserted} companies")
        print(f"❌ FAILED: {failed} companies")
        print("=" * 60)

if __name__ == '__main__':
    inserter = SupabaseInserter()
    inserter.insert_companies('data/verified_companies.json')
