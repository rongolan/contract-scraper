# Contract Scraper Project

## Project Vision
Building a comprehensive portal for all contract opportunities for service businesses in the Massachusetts area (eventually expanding to other states). Starting with municipal contracts as they're easier to scrape consistently, then expanding to commercial opportunities (hospitals, business parks, etc.).

## Current Status
- **Phase**: 🚀 **LIVE PRODUCTION APP** deployed on Heroku
- **Production URL**: https://macontractscraper-18a0ccf5d2d6.herokuapp.com/
- **Goal**: Get feedback from service business owners before investing in full scraper suite
- **Target Users**: Service businesses (landscaping, construction, plumbing, electrical, etc.)

## Working Components
- **5 operational scrapers**: Somerville, Concord, Worcester, Boston, Newton (all enhanced with two-step scraping)
- **Production database**: PostgreSQL on Heroku (Essential-0 plan, $5/month) 
- **Automated scheduling**: Heroku Scheduler running twice daily (6 AM & 5 PM EST)
- **Data integration**: Google Sheets + PostgreSQL database with environment variables
- **Advanced data cleaning**: Date standardization, industry classification, contract values
- **Web UI**: Flask backend with responsive frontend, live filtering, urgency indicators
- **Enhanced scraping**: Boston-specific field mapping (UNSPSC codes, Closes field extraction)

## Scraper Standards
- **Two-step approach**: Always scrape main table + individual bid pages when available
- **Rate limiting**: 1-2 second delays between requests to avoid being blocked
- **Graceful fallback**: Keep basic data if individual pages fail, maintain links for user access

## Technical Setup

### Production Environment (Heroku)
- **Hosting**: Heroku (macontractscraper app)
- **Database**: PostgreSQL Essential-0 ($5/month, 10k rows, 20 connections)
- **Environment**: Python 3.11 with managed dependencies + Chrome/ChromeDriver buildpacks
- **Security**: Environment variables for DATABASE_URL and Google Sheets credentials
- **Scheduling**: Heroku Scheduler running twice daily (6 AM & 5 PM EST / 10:00 & 21:00 UTC)

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

## Current Data Quality Status
1. **Date formats** - ✅ COMPLETED: Standardized to YYYY-MM-DD H:MM AM/PM format with TBD and Month-Year support
2. **Title formatting** - ✅ COMPLETED: Mixed cases, weird characters (partially fixed with regex) - GOOD ENOUGH FOR MVP
3. **Industry classification** - ✅ BASIC COMPLETED: Keyword-based classification into 20+ service business categories (future: LLM enhancement)
4. **Contract values** - ✅ PARTIALLY COMPLETED: Concord scraper extracts values when available; Newton uses open pricing; Somerville upcoming bids have values
5. **Bid page URLs** - ✅ COMPLETED: All cities now provide clickable links to individual bid pages for UI
6. **Boston due dates** - ✅ COMPLETED: Now properly extracts from "Closes" field instead of showing TBD

## Product Development Roadmap
Based on strategic planning session July 29, 2025:

### **Phase 1: URL Structure & Routing Foundation** 🚧 NEXT
- Implement client-side routing for shareable URLs
- Structure: `/` (landing), `/app` (contract search), `/app?city=Boston&industry=Construction` (filtered searches)
- Foundation for user account system

### **Phase 2: User Accounts & Authentication** 
- Email/password authentication system
- User preferences and saved searches
- Role-based permissions (user/admin)
- Admin panel for manual contract data edits
- Database schema: `users`, `user_preferences`, `user_sessions`

### **Phase 3: Landing Page & Marketing**
- Professional landing page explaining value proposition
- Sample data showcase
- Pricing tier information (free vs paid)
- SEO optimization

### **Phase 4: Database Architecture Overhaul**
- Move from full table replacement to incremental updates
- Contract history tracking and status changes
- Manual edit protection with `is_manually_edited` flags  
- More efficient scraper resource usage

### **Phase 5: Performance Optimizations**
- Async scraper execution for faster runs
- Advanced error handling and retry logic

## Previous Milestones (Completed)
1. **User Testing**: ✅ READY - Show live app to local service businesses for focused feedback
2. **Six Municipality Coverage**: ✅ COMPLETED - Somerville, Concord, Worcester, Boston, Newton, Quincy operational
3. **Enhanced Data Quality**: ✅ COMPLETED - Release dates, industry classification, two-step scraping

## Recent Fixes (July 29, 2025)
- **Somerville scraper**: ✅ FIXED - Enhanced title cleaning with improved regex to remove special characters and normalize formatting
- **Worcester scraper**: ✅ FIXED - Fixed Open Date extraction from individual bid pages (now properly extracts from field-bid-posting-open-date structure)
- **Quincy scraper**: ✅ FIXED - Fixed URL construction bug preventing individual bid page access (now successfully scraping enhanced data from all bid pages)

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