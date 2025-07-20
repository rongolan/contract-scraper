# Contract Scraper Project

## Project Vision
Building a comprehensive portal for all contract opportunities for service businesses in the Massachusetts area (eventually expanding to other states). Starting with municipal contracts as they're easier to scrape consistently, then expanding to commercial opportunities (hospitals, business parks, etc.).

## Current Status
- **Phase**: End-to-end working prototype with limited scrapers
- **Goal**: Get feedback from service business owners before investing in full scraper suite
- **Target Users**: Service businesses (landscaping, construction, plumbing, electrical, etc.)

## Working Components
- 4 operational scrapers: Somerville, Newton, Concord, Worcester (enhanced two-step scraping)
- Daily automated scraping at 8am via cron job (with reliable shell script)
- Data uploaded to both Google Sheets and PostgreSQL database
- Advanced data cleaning: date standardization, industry classification, contract values
- Web UI: Flask backend with responsive frontend (running on localhost:5001)

## Scraper Standards
- **Two-step approach**: Always scrape main table + individual bid pages when available
- **Rate limiting**: 1-2 second delays between requests to avoid being blocked
- **Graceful fallback**: Keep basic data if individual pages fail, maintain links for user access

## Technical Setup
- **Environment**: Python virtual environment (`venv/`)
- **Database**: PostgreSQL (localhost:5432, db: contracts, user: scraper)
- **Output**: Google Sheets + PostgreSQL database
- **Scheduling**: Cron job for daily runs

## How to Run
```bash
# Activate virtual environment
source venv/bin/activate

# Run all scrapers manually
python orchestrator.py

# Run the web UI
python app.py
# Then open http://localhost:5001 in browser

# Check logs
tail cron.log
tail log.txt
```

## Current Data Quality Issues (In Progress)
1. **Date formats** - ✅ COMPLETED: Standardized to YYYY-MM-DD H:MM AM/PM format with TBD and Month-Year support
2. **Title formatting** - Mixed cases, weird characters (partially fixed with regex) - GOOD ENOUGH FOR MVP
3. **Industry classification** - ✅ COMPLETED: AI-powered classification into 20+ service business categories
4. **Contract values** - ✅ PARTIALLY COMPLETED: Concord scraper extracts values when available; Newton uses open pricing; Somerville upcoming bids have values
5. **Bid page URLs** - ✅ COMPLETED: All cities now provide clickable links to individual bid pages for UI

## Next Steps
1. **User Testing**: ✅ UI COMPLETED - Show prototype to local service businesses for focused feedback
2. **Enhanced Scraping**: Extract contract values from PDFs/linked documents (Somerville open bids)
3. **UI Improvements**: Iterate based on real user feedback
4. **Additional Scrapers**: Expand to more Massachusetts municipalities
5. **Document Downloads**: Implement PDF document download functionality

## Future Expansion
- Additional municipalities in MA
- Commercial opportunities (hospitals, business parks, corporate RFPs)
- Other states
- Search functionality (fast follow after initial feedback)

## File Structure
- `orchestrator.py` - Main coordinator
- `app.py` - Flask web server for UI
- `run_scraper_cron.sh` - Reliable cron script
- `templates/index.html` - Web UI frontend
- `scrapers/` - Individual city scrapers:
  - `somerville.py` - Somerville scraper
  - `newton.py` - Newton scraper  
  - `concord.py` - Concord scraper
  - `cambridge.py` - Cambridge scraper (postponed)
  - `cambridge_api.py` - Cambridge API utilities
- `google_sheets_credentials.json` - Google API credentials
- `cron.log` - Automated run logs

## Known Issues & Future Platforms
- **Cambridge scraper**: Uses OpenGov.com platform with anti-scraping protection - postponed for later
- Focus on prototype completeness over scraper quantity initially
- Data normalization includes status bucketing (Open/Upcoming/Closed)

## Third-Party Platforms to Crack (Future Development)
- **CivicEngage**: Used by Lowell and many other municipalities - cracking this unlocks multiple cities
- **OpenGov.com**: Used by Cambridge with anti-scraping - challenging but high-value if solved
- **COMMBUYS**: Massachusetts state procurement system used by Springfield and others - API approach needed