# Contract Scraper Project

## Project Vision
Building a comprehensive portal for all contract opportunities for service businesses in the Massachusetts area (eventually expanding to other states). Starting with municipal contracts as they're easier to scrape consistently, then expanding to commercial opportunities (hospitals, business parks, etc.).

## Current Status
- **Phase**: 🚀 **LIVE PRODUCTION APP** deployed on Heroku
- **Production URL**: https://macontractscraper-18a0ccf5d2d6.herokuapp.com/
- **Goal**: Get feedback from service business owners before investing in full scraper suite
- **Target Users**: Service businesses (landscaping, construction, plumbing, electrical, etc.)

## Working Components
- **4 operational scrapers**: Somerville, Concord, Worcester, Boston (enhanced two-step scraping)
- **Newton scraper**: Temporarily disabled (requires Chrome setup for Heroku deployment)
- **Production database**: PostgreSQL on Heroku (Essential-0 plan, $5/month)
- **Data integration**: Google Sheets + PostgreSQL database with environment variables
- **Advanced data cleaning**: Date standardization, industry classification, contract values
- **Web UI**: Flask backend with responsive frontend, live filtering, urgency indicators
- **Enhanced scraping**: Boston-specific field mapping (UNSPSC codes, Type classification)

## Scraper Standards
- **Two-step approach**: Always scrape main table + individual bid pages when available
- **Rate limiting**: 1-2 second delays between requests to avoid being blocked
- **Graceful fallback**: Keep basic data if individual pages fail, maintain links for user access

## Technical Setup

### Production Environment (Heroku)
- **Hosting**: Heroku (macontractscraper app)
- **Database**: PostgreSQL Essential-0 ($5/month, 10k rows, 20 connections)
- **Environment**: Python 3.11 with managed dependencies
- **Security**: Environment variables for DATABASE_URL and Google Sheets credentials
- **Scheduling**: Ready for Heroku Scheduler (cron replacement)

### Local Development Environment  
- **Environment**: Python virtual environment (`venv/`)
- **Database**: PostgreSQL (localhost:5432, db: contracts, user: scraper)
- **Output**: Google Sheets + PostgreSQL database
- **Scheduling**: Cron job for daily runs

## How to Run

### Production (Heroku)
```bash
# Run scrapers manually on Heroku
heroku run python orchestrator.py

# View live app
heroku open
# Or visit: https://macontractscraper-18a0ccf5d2d6.herokuapp.com/

# Check Heroku logs
heroku logs --tail
```

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run all scrapers manually
python orchestrator.py

# Run the web UI locally
python app.py
# Then open http://localhost:5001 in browser

# Check local logs
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

## Deployment (Heroku)
- **Platform**: Heroku Basic ($7/month budget, using $5/month database)
- **App Name**: macontractscraper
- **Database**: PostgreSQL Essential-0 
- **Environment Variables**: DATABASE_URL, GOOGLE_SHEETS_CREDENTIALS_JSON
- **Deployment**: Git-based (push to heroku main branch)
- **Status**: ✅ LIVE and operational

## File Structure
- `orchestrator.py` - Main coordinator (production-ready with environment variables)
- `app.py` - Flask web server for UI (production-ready)
- `requirements.txt` - Python dependencies for Heroku
- `Procfile` - Heroku deployment configuration
- `runtime.txt` - Python version specification
- `.env.example` - Environment variable template
- `run_scraper_cron.sh` - Local cron script (not used in production)
- `templates/index.html` - Web UI frontend
- `scrapers/` - Individual city scrapers:
  - `somerville.py` - Somerville scraper
  - `newton.py` - Newton scraper (temporarily disabled for Heroku)
  - `concord.py` - Concord scraper
  - `worcester.py` - Worcester scraper (enhanced two-step)
  - `boston.py` - Boston scraper (enhanced with UNSPSC mapping)
  - `cambridge.py` - Cambridge scraper (postponed)
- `google_sheets_credentials.json` - Google API credentials (local only)
- `cron.log` - Local automated run logs

## Known Issues & Future Platforms
- **Cambridge scraper**: Uses OpenGov.com platform with anti-scraping protection - postponed for later
- Focus on prototype completeness over scraper quantity initially
- Data normalization includes status bucketing (Open/Upcoming/Closed)

## Third-Party Platforms to Crack (Future Development)
- **CivicEngage**: Used by Lowell and many other municipalities - cracking this unlocks multiple cities
- **OpenGov.com**: Used by Cambridge with anti-scraping - challenging but high-value if solved
- **COMMBUYS**: Massachusetts state procurement system used by Springfield and others - API approach needed