# Contract Scraper Project

## Project Vision
Building a comprehensive portal for all contract opportunities for service businesses in the Massachusetts area (eventually expanding to other states). Starting with municipal contracts as they're easier to scrape consistently, then expanding to commercial opportunities (hospitals, business parks, etc.).

## Business Model
**Freemium SaaS model** designed for service business owners who need efficient contract discovery:

### **Free Accounts** 
- ✅ Full access to contract browsing and filtering
- ✅ Complete search capabilities across all municipalities
- ✅ Basic account creation and login
- ❌ No saved preferences or notifications
- ❌ No personalized homepage/feed

### **Paid Accounts** (Future Implementation)
- ✅ All free features plus:
- ✅ Saved search preferences and filters
- ✅ Email notifications for new relevant contracts
- ✅ Personalized homepage feed based on preferences
- ✅ Advanced filtering and alerting options
- ✅ Priority customer support

### **Target Market**
Service businesses (landscaping, construction, plumbing, electrical, HVAC, etc.) who value time-saving automation over manual contract searching. Paid tier focuses on convenience features that justify recurring subscription costs.

## Current Status
- **Phase**: 🚀 **PHASE 2 COMPLETED** - Full Authentication System Live on Heroku
- **Production URL**: https://macontractscraper-18a0ccf5d2d6.herokuapp.com/
- **Authentication**: ✅ User login/signup, admin panel, role-based access deployed
- **Admin Access**: golansron@gmail.com with full system management capabilities
- **Goal**: Show complete system to service business owners for feedback before Phase 3
- **Target Users**: Service businesses (landscaping, construction, plumbing, electrical, etc.)

## Working Components
- **6 operational scrapers**: Somerville, Concord, Worcester, Boston, Newton, Quincy (all enhanced with two-step scraping)
- **Full user authentication system**: Registration, login, role-based access (user/admin), session management
- **Admin panel**: User management, system administration with golansron@gmail.com admin account
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
# Set up authentication database on Heroku (first time only)
heroku run python deploy_to_heroku.py

# Run scrapers manually on Heroku
heroku run python orchestrator.py

# View live app with authentication
heroku open
# Or visit: https://macontractscraper-18a0ccf5d2d6.herokuapp.com/
# Admin login: golansron@gmail.com / SecureAdmin2025!

# Check Heroku logs
heroku logs --tail
```

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Set up authentication database (first time only)
python setup_database.py

# Run all scrapers manually
python orchestrator.py

# Run the web UI locally (with authentication)
python app.py
# Then open http://localhost:5001 in browser
# Admin login: golansron@gmail.com / AdminPass123!

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

### **Phase 1: URL Structure & Routing Foundation** ✅ COMPLETED
- ✅ Implemented client-side routing for shareable URLs
- ✅ Structure: `/` (landing), `/home` (authenticated users), `/contracts` (contract search), filterable URLs
- ✅ Fixed router path matching bugs with browser navigation
- ✅ Foundation for user account system established

### **Phase 2: User Accounts & Authentication** ✅ COMPLETED
- ✅ Email/password authentication system with Flask-Login
- ✅ User preferences and saved searches capability
- ✅ Role-based permissions (user/admin) fully implemented
- ✅ Admin panel for system management
- ✅ Database schema: `users`, `user_preferences`, `user_sessions` deployed
- ✅ Admin user created: golansron@gmail.com
- ✅ Password strength validation and secure hashing

### **Phase 3: Landing Page & Marketing + User Journey Implementation** 🚧 NEXT

#### **Phase 3A: Logged Out & Free Account Experience**
- ✅ Professional landing page explaining value proposition
- ✅ Conditional navigation (hide My Feed for logged-out users)
- ✅ Browse Contracts placeholder with signup prompt for logged-out users
- ✅ Updated My Feed placeholder for premium features
- ✅ About page (blank template for now)
- ✅ Settings → Preferences rename with upgrade prompts for free users
- ✅ Logo routing: landing page (logged out) → Browse Contracts (free account)
- ✅ Remove landing page access for authenticated users

#### **Phase 3B: Paid Account Features** (Future Implementation)
- Paid account type differentiation in user model
- Logo routing to personalized feed for paid users
- Actual My Feed functionality with customized contract feeds
- Subscription/payment integration
- Saved preferences and notification system

### **Phase 4: Database Architecture Overhaul**
- Move from full table replacement to incremental updates
- Contract history tracking and status changes
- Manual edit protection with `is_manually_edited` flags  
- More efficient scraper resource usage

### **Phase 5: Performance Optimizations**
- Async scraper execution for faster runs
- Advanced error handling and retry logic

## Previous Milestones (Completed)
1. **Six Municipality Coverage**: ✅ COMPLETED - Somerville, Concord, Worcester, Boston, Newton, Quincy operational
2. **Enhanced Data Quality**: ✅ COMPLETED - Release dates, industry classification, two-step scraping
3. **URL Routing Foundation**: ✅ COMPLETED - Client-side routing, shareable URLs, navigation bug fixes
4. **User Authentication System**: ✅ COMPLETED - Full login/signup, admin panel, role-based access, deployed to production
5. **User Testing**: ✅ READY - Show live app with authentication to service business owners for feedback

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
- **Environment Variables**: DATABASE_URL, GOOGLE_SHEETS_CREDENTIALS_JSON, SECRET_KEY
- **Deployment**: Git-based (push to heroku main branch)
- **Status**: ✅ LIVE and operational

## File Structure
- `orchestrator.py` - Main coordinator (production-ready with environment variables)
- `app.py` - Flask web server with authentication system (production-ready)
- `models.py` - User authentication models and database utilities
- `setup_database.py` - Local database setup script for authentication tables
- `deploy_to_heroku.py` - Heroku database setup and admin user creation
- `AUTHENTICATION_SETUP.md` - Complete authentication system documentation
- `requirements.txt` - Python dependencies for Heroku
- `Procfile` - Heroku deployment configuration
- `runtime.txt` - Python version specification
- `.env.example` - Environment variable template (includes authentication secrets)
- `run_scraper_cron.sh` - Local cron script (not used in production)
- `templates/index.html` - Single-page application with authentication UI
- `scrapers/` - Individual city scrapers:
  - `somerville.py` - Somerville scraper
  - `newton.py` - Newton scraper
  - `concord.py` - Concord scraper
  - `worcester.py` - Worcester scraper (enhanced two-step)
  - `boston.py` - Boston scraper (enhanced with UNSPSC mapping)
  - `quincy.py` - Quincy scraper (enhanced two-step)
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