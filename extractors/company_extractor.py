"""
extract company data from articles
"""

import re
from typing import Optional, List
from bs4 import BeautifulSoup


class CompanyExtractor:
    """extract company information from html/text"""

    # sector keywords
    SECTOR_KEYWORDS = {
        'fintech': ['payment', 'fintech', 'bank', 'wallet', 'transfer', 'lending', 'credit', 'loan', 'investment', 'savings'],
        'healthtech': ['health', 'medical', 'hospital', 'clinic', 'pharma', 'telemedicine', 'healthcare', 'doctor'],
        'edtech': ['education', 'learning', 'school', 'tutor', 'edtech', 'student', 'course', 'elearning'],
        'agritech': ['farm', 'agric', 'crop', 'agritech', 'agriculture', 'farmer'],
        'logistics': ['logistics', 'delivery', 'shipping', 'transport', 'courier', 'dispatch'],
        'ecommerce': ['ecommerce', 'e-commerce', 'marketplace', 'retail', 'shop', 'shopping', 'online store'],
        'saas': ['software', 'saas', 'platform', 'api', 'cloud', 'tool'],
    }

    @classmethod
    def extract_company_name(cls, soup: BeautifulSoup, title: str = '') -> Optional[str]:
        """extract actual company name from article content"""
        # try to get from title or heading
        if not title:
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                title = title_elem.get_text().strip()

        if not title:
            return None

        # skip articles that are listicles (7 startups, 5 companies, etc.)
        if re.search(r'\d+\s+(?:african\s+)?(?:startups|companies)', title, re.IGNORECASE):
            return None

        # skip if title is too long (likely a full sentence/headline)
        if len(title) > 100:
            return None

        # pattern 0: "Day X-Y of CompanyName" (series format)
        match = re.search(r'day\s+\d+-\d+\s+of\s+([A-Z][A-Za-z0-9]+)', title, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and len(name) < 30:
                return name

        # get first non-empty paragraph for context
        first_para = ''
        article_body_candidates = [
            soup.find('div', class_=re.compile(r'entry-content|article-content|post-content')),
            soup.find('article'),
        ]

        for article_body in article_body_candidates:
            if article_body:
                paragraphs = article_body.find_all('p')
                for p in paragraphs:
                    text = p.get_text().strip()
                    if len(text) > 20:
                        first_para = text
                        break
                if first_para:
                    break

        # pattern 1: "Company Name, a fintech startup..."
        match = re.search(r'^([A-Z][A-Za-z0-9\s&]+),\s+a\s+(?:nigerian|african|kenyan)?\s*(?:fintech|healthtech|edtech|agritech|startup|company)', first_para)
        if match:
            name = match.group(1).strip()
            if len(name) < 50:
                return name

        # pattern 2: "Company Name is a..."
        match = re.search(r'^([A-Z][A-Za-z0-9\s&]+)\s+is\s+a\s+(?:nigerian|african|kenyan)?\s*(?:fintech|healthtech|edtech|startup|platform|company)', first_para)
        if match:
            name = match.group(1).strip()
            if len(name) < 50:
                return name

        # pattern 3: "Company Name has raised..."
        match = re.search(r'^([A-Z][A-Za-z0-9\s&]+)\s+(?:has\s+)?(?:raised|secured|announced)', first_para)
        if match:
            name = match.group(1).strip()
            # must be short (real company name, not sentence)
            if len(name) < 30 and not any(word in name.lower() for word in ['the', 'after', 'how', 'when', 'what', 'this']):
                return name

        # pattern 4: from title - "How CompanyName is building..."
        match = re.search(r'(?:how|why)\s+([A-Z][A-Za-z0-9\s&]+)\s+is\s+(?:building|transforming|creating)', title, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) < 30:
                return name

        # pattern 5: "CompanyName raises $X..." or "CompanyName turns profit"
        match = re.search(r'^([A-Z][A-Za-z0-9\s&\'\-\.]+)\s+(?:raises|secures|gets|receives|adopts|launches|turns|announces|opens|sets)', title)
        if match:
            name = match.group(1).strip()
            # clean common prefixes
            name = re.sub(r'^(?:nigeria\'?s|kenya\'?s|african)\s+', '', name, flags=re.IGNORECASE).strip()
            # clean descriptive prefixes like "voice tech startup", "fintech startup", etc
            name = re.sub(r'(?:voice\s+tech|fintech|healthtech|edtech|agritech|proptech|insurtech|regtech)\s+startup\s+', '', name, flags=re.IGNORECASE).strip()
            if len(name) < 30 and len(name) > 2:
                return name

        # pattern 6a: "When/After ... CompanyName ..." (handles special chars like é)
        match = re.search(r'(?:when|after)\s+.*?,\s+([A-Z][A-Za-zÀ-ÿ0-9\'\-\.]+)\s+(?:bets|wants|believes|thinks)', title, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) < 30 and len(name) > 2:
                return name

        # pattern 6: look for capitalized words in first sentence
        match = re.search(r'^([A-Z][A-Za-z0-9]+)(?:\s+[A-Z][A-Za-z]+)?\s*,', first_para)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and len(name) < 20:
                return name

        return None

    @classmethod
    def extract_sector(cls, text: str) -> str:
        """determine sector from text content"""
        if not text:
            return 'other'

        text_lower = text.lower()

        # count matches for each sector
        sector_scores = {}
        for sector, keywords in cls.SECTOR_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                sector_scores[sector] = score

        # return sector with highest score
        if sector_scores:
            return max(sector_scores, key=sector_scores.get)

        return 'other'

    @classmethod
    def is_nigerian_company(cls, text: str, title: str = '') -> bool:
        """check if company is nigerian using scoring system"""
        combined_text = (title + ' ' + text).lower()

        # count nigerian indicators
        nigerian_indicators = [
            'nigeria', 'nigerian', 'lagos', 'abuja', 'port harcourt',
            'ibadan', 'kano', 'enugu', 'based in nigeria',
            'nigerian startup', 'nigerian fintech', 'nigerian healthtech'
        ]

        nigerian_score = 0
        for indicator in nigerian_indicators:
            count = combined_text.count(indicator)
            nigerian_score += count

        # count mentions of other african countries
        other_countries = [
            'kenya', 'kenyan', 'nairobi',
            'south africa', 'south african', 'cape town', 'johannesburg',
            'ghana', 'ghanaian', 'accra',
            'rwanda', 'rwandan', 'kigali',
            'zimbabwe', 'zimbabwean', 'harare',
            'uganda', 'ugandan', 'kampala',
            'tanzania', 'tanzanian', 'dar es salaam',
            'senegal', 'senegalese', 'dakar',
            'mali', 'malian', 'bamako',
            'egypt', 'egyptian', 'cairo'
        ]

        other_score = 0
        for country in other_countries:
            count = combined_text.count(country)
            other_score += count

        # decision logic: nigerian score must be higher than other countries
        # and must have at least 2 nigerian mentions
        if nigerian_score >= 2 and nigerian_score > other_score:
            return True

        # if no other countries mentioned and nigeria mentioned at least once
        if other_score == 0 and nigerian_score >= 1:
            return True

        return False

    @classmethod
    def extract_description(cls, soup: BeautifulSoup, max_length: int = 500) -> Optional[str]:
        """extract article description or excerpt"""
        # try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc = meta_desc['content'].strip()
            if len(desc) > 20:
                return desc[:max_length]

        # try article excerpt
        excerpt = soup.find('div', class_=re.compile(r'excerpt|summary|intro'))
        if excerpt:
            desc = excerpt.get_text().strip()
            if len(desc) > 20:
                return desc[:max_length]

        # try first paragraph in article body
        article_body = soup.find('article') or soup.find('div', class_=re.compile(r'entry-content|article-content|post-content'))
        if article_body:
            paragraphs = article_body.find_all('p')
            for p in paragraphs[:3]:
                text = p.get_text().strip()
                if len(text) > 50:
                    return text[:max_length]

        return None

    @classmethod
    def extract_website(cls, soup: BeautifulSoup, text: str) -> Optional[str]:
        """try to find company website url"""
        # look for links to company website
        links = soup.find_all('a', href=True)

        for link in links:
            href = link['href']
            link_text = link.get_text().lower()

            # skip social media and news sites
            exclude_domains = [
                'twitter.com', 'facebook.com', 'linkedin.com', 'instagram.com',
                'techcabal.com', 'techpoint.africa', 'youtube.com'
            ]

            if any(domain in href for domain in exclude_domains):
                continue

            # look for "visit website" or similar text
            if any(word in link_text for word in ['visit', 'website', 'official']):
                return href

        # try to find urls in text
        url_pattern = r'https?://(?:www\.)?([a-zA-Z0-9-]+\.(?:com|ng|co|io|africa))'
        matches = re.findall(url_pattern, text)

        if matches:
            # return first non-news site
            for match in matches:
                if not any(news in match for news in ['techcabal', 'techpoint', 'disrupt']):
                    return f"https://{match}"

        return None

    @classmethod
    def extract_founders(cls, text: str) -> List[str]:
        """extract founder names from text"""
        if not text:
            return []

        founders = []

        # patterns for founder extraction
        patterns = [
            r'founded by ([A-Z][a-z]+ [A-Z][a-z]+(?:,? (?:and )?[A-Z][a-z]+ [A-Z][a-z]+)*)',
            r'co-founded by ([A-Z][a-z]+ [A-Z][a-z]+(?:,? (?:and )?[A-Z][a-z]+ [A-Z][a-z]+)*)',
            r'founder[s]?,?\s+([A-Z][a-z]+ [A-Z][a-z]+(?:,? (?:and )?[A-Z][a-z]+ [A-Z][a-z]+)*)',
            r'CEO,?\s+([A-Z][a-z]+ [A-Z][a-z]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # split by "and" or commas
                names = re.split(r',?\s+and\s+|,\s*', match)
                for name in names:
                    name = name.strip()
                    if len(name) > 3 and name not in founders:
                        founders.append(name)

        return founders[:5]  # limit to 5 founders max
