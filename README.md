# WebScrappingL

Learning-focused repository for **web scraping** practice to support a final year research project.

## Goal
Build practical web scraping skills and produce clean, research-ready datasets.

## Learning Roadmap
1. **Basics (Week 1)**
   - Learn HTML structure (`tags`, `classes`, `ids`)
   - Practice with Python `requests` and `BeautifulSoup`
2. **Dynamic Pages (Week 2)**
   - Handle JavaScript-rendered content with Selenium or Playwright
   - Extract paginated results
3. **Data Quality (Week 3)**
   - Clean and normalize collected data
   - Save outputs as CSV/JSON for analysis
4. **Research Integration (Week 4)**
   - Define scraping targets based on research questions
   - Document methodology for reproducibility

## Suggested Workflow
1. Pick one small website/page for practice.
2. Inspect page structure with browser developer tools.
3. Write a scraper for one data field first, then expand.
4. Add error handling and polite delays between requests.
5. Store cleaned outputs in a consistent schema.

## Responsible Scraping Checklist
- Check `robots.txt` and site terms before scraping.
- Avoid overloading websites (rate-limit your requests).
- Do not scrape private or restricted data.
- Keep a log of source URLs and timestamps for research transparency.

## Next Milestones
- [ ] Create first scraper script for a static page
- [ ] Extract at least 100 records into CSV
- [ ] Validate data quality (missing values, duplicates)
- [ ] Prepare a short method note for the final year research report