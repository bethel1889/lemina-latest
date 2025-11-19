# data sources inventory

comprehensive list of sources for nigerian startup data collection.

## tier 1 sources (high priority - must scrape)

### news & media outlets
1. **techcabal** (techcabal.com)
   - coverage: nigerian tech news, funding announcements, product launches
   - data: company profiles, funding rounds, metrics, founder info
   - frequency: daily updates
   - reliability: high (90/100)

2. **techpoint africa** (techpoint.africa)
   - coverage: african startup ecosystem, detailed company profiles
   - data: funding, team size, business models, traction metrics
   - frequency: daily updates
   - reliability: high (90/100)

3. **disrupt africa** (disrupt-africa.com)
   - coverage: funding announcements, startup launches
   - data: investment amounts, investors, round types
   - frequency: several times per week
   - reliability: high (85/100)

4. **nairametrics** (nairametrics.com)
   - coverage: business news, financial data, valuations
   - data: revenue figures, financial metrics, regulatory updates
   - frequency: daily updates
   - reliability: medium-high (80/100)

5. **the big deal** (bigdeal.substack.com)
   - coverage: african startup funding tracker
   - data: comprehensive funding database, amounts, investors
   - frequency: weekly newsletter
   - reliability: very high (95/100) - specializes in funding data
   - note: structured data, easier to parse

### structured databases
6. **crunchbase** (crunchbase.com)
   - coverage: global startup database with african coverage
   - data: comprehensive profiles, funding history, founders, investors
   - access: free tier api (limited) or web scraping
   - reliability: very high (95/100)
   - note: rate limits apply

7. **african tech roundup** (africantechroundup.com)
   - coverage: curated weekly startup news
   - data: funding rounds, launches, acquisitions
   - frequency: weekly
   - reliability: high (85/100)

### company direct sources
8. **company websites** (direct scraping)
   - coverage: all companies
   - data: about pages, team pages, product info, contact details
   - reliability: high (90/100) - primary source
   - note: self-reported but authoritative

## tier 2 sources (medium priority - valuable data)

### specialized trackers
9. **briter bridges** (briterbridges.com)
   - coverage: african vc funding data
   - data: detailed funding rounds, investor networks
   - reliability: high (85/100)
   - note: some data behind paywall

10. **partech africa reports** (partechpartners.com)
    - coverage: annual african tech funding reports
    - data: funding trends, top deals, sector breakdowns
    - frequency: annual + quarterly updates
    - reliability: very high (95/100)

11. **vc firm blogs & announcements**
    - ventures platform blog (venturesplatform.com/blog)
    - tlcom capital (tlcomcapital.com/news)
    - egypts flat6labs (flat6labs.com/news)
    - future africa (future.africa/blog)
    - coverage: portfolio announcements, funding details
    - data: investment amounts, deal terms, company updates
    - reliability: very high (95/100) - direct from investors

### business publications
12. **african business** (africanbusinessmagazine.com)
    - coverage: african business trends, startup features
    - data: company profiles, expansion plans, financials
    - frequency: monthly magazine + daily online
    - reliability: high (85/100)

13. **techcrunch** (techcrunch.com/tag/africa)
    - coverage: major african tech deals
    - data: large funding rounds, acquisitions, unicorns
    - frequency: occasional african coverage
    - reliability: very high (95/100)
    - note: only covers major deals

14. **bloomberg** (bloomberg.com - search african startups)
    - coverage: major deals, financial data, valuations
    - data: funding amounts, market size estimates
    - reliability: very high (95/100)
    - note: limited african coverage, paywall

### regulatory sources
15. **central bank of nigeria** (cbn.gov.ng)
    - coverage: licensed payment service providers, microfinance banks
    - data: license numbers, approval dates, license types
    - frequency: quarterly license list updates
    - reliability: absolute (100/100) - official source
    - pages: "approved psps", "licensed institutions"

16. **corporate affairs commission** (cac.gov.ng)
    - coverage: company registrations, cac numbers
    - data: registration status, company type, directors
    - reliability: absolute (100/100) - official source
    - note: requires company name search

17. **securities and exchange commission** (sec.gov.ng)
    - coverage: registered investment advisors, capital market operators
    - data: registration status, license types
    - reliability: absolute (100/100) - official source

18. **naicom** (naicom.gov.ng)
    - coverage: licensed insurance companies
    - data: license status for insurtech companies
    - reliability: absolute (100/100) - official source

### social & community sources
19. **linkedin** (linkedin.com/company/*)
    - coverage: company pages, founder profiles
    - data: employee count, founder backgrounds, job postings
    - reliability: high (85/100)
    - note: limited without authentication, requires careful scraping

20. **twitter/x** (twitter.com)
    - coverage: company announcements, founder updates
    - data: product launches, metrics shared publicly, news
    - reliability: medium (70/100) - unverified claims
    - note: requires twitter api or scraping

21. **angel.co / wellfound** (wellfound.com)
    - coverage: startup profiles, jobs, fundraising
    - data: team size, funding status, job openings
    - reliability: high (85/100)

## tier 3 sources (low priority - supplementary)

### metrics & analytics platforms
22. **getlatka** (getlatka.com)
    - coverage: saas metrics for some african startups
    - data: revenue estimates, user counts, growth rates
    - reliability: medium (70/100) - estimates
    - note: limited african coverage

23. **similarweb** (similarweb.com)
    - coverage: website traffic estimates
    - data: monthly visits, traffic sources, engagement
    - reliability: medium (65/100) - estimates
    - note: free tier limited

24. **app store / play store**
    - coverage: mobile app metrics
    - data: download ranges, ratings, reviews, last updated
    - reliability: high (85/100) - official app data
    - note: download counts in ranges (10k-50k)

### community & newsletters
25. **benjamin dada's newsletter** (benjamindada.com)
    - coverage: african tech insights, funding news
    - data: funding announcements, analysis
    - frequency: weekly
    - reliability: high (85/100)

26. **africaarena** (africaarena.com)
    - coverage: startup competition, ecosystem reports
    - data: participating startups, awards, profiles
    - frequency: annual event + ongoing updates
    - reliability: medium-high (80/100)

27. **tracxn** (tracxn.com)
    - coverage: startup tracking platform
    - data: funding, investors, metrics
    - reliability: high (85/100)
    - note: mostly behind paywall

### startup directories
28. **ycombinator directory** (ycombinator.com/companies)
    - coverage: nigerian companies in yc
    - data: batch year, one-liner, founders
    - reliability: high (90/100)

29. **500 global portfolio** (500.co/companies)
    - coverage: nigerian portfolio companies
    - data: funding, sectors, descriptions
    - reliability: high (90/100)

## data extraction priority matrix

### for company profiles
- tier 1: company website, techcabal, techpoint, crunchbase
- tier 2: linkedin, african business, vc firm blogs
- tier 3: twitter, angel.co

### for funding rounds
- tier 1: the big deal, disrupt africa, techpoint, techcabal
- tier 2: crunchbase, vc firm announcements, techcrunch
- tier 3: briter bridges, partech reports

### for regulatory data
- tier 1: cbn, cac, sec, naicom (official sources)
- tier 2: company announcements, techcabal, nairametrics
- tier 3: twitter, linkedin

### for metrics/traction
- tier 1: company websites, press releases, nairametrics
- tier 2: techpoint, techcabal, getlatka
- tier 3: similarweb, app stores, linkedin employee count

### for founder data
- tier 1: linkedin, company about pages
- tier 2: techpoint founder profiles, crunchbase
- tier 3: twitter, forbes africa lists

## scraping difficulty assessment

**easy (static html, no auth required):**
- company websites
- techcabal
- techpoint
- disrupt africa
- nairametrics
- african business
- cbn license lists

**medium (may have js rendering, pagination):**
- the big deal (substack)
- vc firm blogs
- crunchbase (rate limited)
- cac website (search required)
- angel.co

**hard (requires auth, complex js, anti-scraping):**
- linkedin (needs careful approach)
- twitter (api preferred, rate limits)
- briter bridges (paywall)
- tracxn (paywall)
- bloomberg (paywall)

**apis available (preferred over scraping):**
- crunchbase (limited free tier)
- twitter api (free tier available)
- exchangerate api (for currency conversion)

## recommended starting sources (phase 1)

focus on these 10 sources for initial implementation:
1. techcabal - comprehensive nigerian coverage
2. techpoint africa - detailed profiles
3. the big deal - best funding data
4. disrupt africa - funding announcements
5. nairametrics - financial data
6. company websites - primary source
7. cbn website - regulatory data
8. vc firm blogs (top 3-5 vcs) - investment details
9. crunchbase - structured data via api
10. linkedin company pages - team size, employee data

this covers 80% of valuable data with manageable complexity.
