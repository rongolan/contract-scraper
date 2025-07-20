from scrapers import somerville
#from scrapers.cambridge import scrape as scrape_cambridge  
from scrapers.concord import scrape as scrape_concord
from scrapers.newton import scrape as scrape_newton
from scrapers.worcester import scrape as scrape_worcester
from scrapers.boston import scrape as scrape_boston
import pandas as pd
import dateparser
from sqlalchemy import create_engine
import os
import json
from urllib.parse import urlparse

# ----------------------------
# Run all scrapers
# ----------------------------
df_somerville = somerville.scrape()
#df_cambridge = scrape_cambridge()
#print("🔍 Cambridge rows scraped:", len(df_cambridge))
df_concord = scrape_concord()
print("🔍 Concord rows scraped:", len(df_concord))
df_newton = scrape_newton()
print("🔍 Newton rows scraped:", len(df_newton))
df_worcester = scrape_worcester()
print("🔍 Worcester rows scraped:", len(df_worcester))
df_boston = scrape_boston()
print("🔍 Boston rows scraped:", len(df_boston))

# Combine safely
dfs = [df for df in [df_somerville, df_concord, df_newton, df_worcester, df_boston] if not df.empty]
if dfs:
    df_combined = pd.concat(dfs, ignore_index=True)
    # --- Normalize and bucket Status column ---
    # Rename lowercase 'status' to 'Status' if present
    if 'status' in df_combined.columns:
        df_combined.rename(columns={'status': 'Status'}, inplace=True)
    # Standardize casing and bucket into Open, Upcoming, Closed
    if 'Status' in df_combined.columns:
        df_combined['Status'] = (
            df_combined['Status']
            .astype(str)
            .str.strip()
            .str.lower()
            .str.capitalize()
        )
        df_combined['Status'] = df_combined['Status'].apply(
            lambda x: 'Open' if x == 'Open' else 'Upcoming' if x == 'Upcoming' else 'Closed'
        )
    # --- Clean up Title prefixes ---
    if 'Title' in df_combined.columns:
        df_combined['Title'] = (
            df_combined['Title']
            .astype(str)
            .str.replace(
                r'^(?:IFB\s*#?\d+-\d+\s+|RFP\s*\d+-\d+\s+|RFS\s*\d+-\d+\s+|Request for Quotes\s*\d{4}-\d+\s+)',
                '',
                regex=True
            )
            .str.strip()
            .str.title()
        )
    # --- Standardize date fields for display ---
    import re
    from datetime import datetime
    
    def standardize_date_for_display(date_str):
        """
        Convert various date formats to standardized display format:
        - Full datetime: "2025-06-18 3:00 PM" 
        - Date only: "2025-06-18"
        - Month-Year: "Nov 2025" (for upcoming planning phase bids)
        """
        if not date_str or str(date_str).lower() in ('', 'nan', 'none'):
            return None
            
        date_str = str(date_str).strip()
        
        # Handle Month-Year only (upcoming bids in planning phase)
        month_year_match = re.match(r'^([A-Za-z]+)\s+(\d{4})$', date_str)
        if month_year_match:
            return date_str  # Keep as-is for planning phase display
            
        # Handle TBD dates (to be determined)
        if 'TBD' in date_str.upper():
            # Extract year if present: "TBD/01/2025" -> "2025 TBD"
            year_match = re.search(r'(\d{4})', date_str)
            if year_match:
                return f"{year_match.group(1)} TBD"
            else:
                return "TBD"
            
        # Try parsing with dateparser first (handles most formats)
        try:
            parsed = dateparser.parse(date_str)
            if parsed:
                # Format for display
                if parsed.time() != datetime.min.time():  # Has time component
                    return parsed.strftime("%Y-%m-%d %I:%M %p")
                else:  # Date only
                    return parsed.strftime("%Y-%m-%d")
        except:
            pass
            
        # Fallback patterns for common formats
        patterns = [
            # "Wed, 05/28/2025 - 12:00pm" or "06/18/2025 - 3:00pm"
            (r'(?:\w+,?\s*)?(\d{1,2})/(\d{1,2})/(\d{4})\s*-?\s*(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)', 'datetime'),
            # "05/28/2025" or "06/18/2025"  
            (r'(?:\w+,?\s*)?(\d{1,2})/(\d{1,2})/(\d{4})', 'date'),
        ]
        
        for pattern, format_type in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if format_type == 'datetime':
                        month, day, year, hour, minute, ampm = match.groups()
                        hour = int(hour)
                        if ampm.upper() == 'PM' and hour != 12:
                            hour += 12
                        elif ampm.upper() == 'AM' and hour == 12:
                            hour = 0
                        dt = datetime(int(year), int(month), int(day), hour, int(minute))
                        return dt.strftime("%Y-%m-%d %I:%M %p")
                    else:  # date only
                        month, day, year = match.groups()
                        dt = datetime(int(year), int(month), int(day))
                        return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
                    
        # If all parsing fails, keep original for manual review
        print(f"⚠️  Could not parse date: '{date_str}' - keeping original")
        return date_str

    # Process date columns
    date_cols = [col for col in df_combined.columns if 'Date' in col]
    
    for col in date_cols:
        print(f"📅 Standardizing {col}...")
        
        # Create raw backup column
        df_combined[col + '_Raw'] = df_combined[col].copy()
        
        # Create standardized display column
        df_combined[col + '_Display'] = df_combined[col].apply(standardize_date_for_display)
        
        # Drop original column (we have Raw and Display now)
        df_combined.drop(columns=[col], inplace=True)
        
    # --- Industry Classification ---
    def classify_industry(title, department=None):
        """
        Classify contract into industry categories based on title and department.
        Uses existing categories from the database.
        """
        if not title:
            return "Other"
            
        title_lower = str(title).lower()
        dept_lower = str(department).lower() if department else ""
        
        # Industry classification rules based on keywords
        classification_rules = {
            "Construction (Buildings)": [
                "school", "building", "construction", "demolition", "renovation", "roof", 
                "foundation", "structural", "facility", "elementary", "boiler", "hvac"
            ],
            "Construction (Public Works, Parks, Roadways)": [
                "roadway", "street", "sidewalk", "park", "playground", "asphalt", "paving", 
                "infrastructure", "sewer", "water main", "drainage", "bridge", "entrance improvements"
            ],
            "Energy and Electrical Services": [
                "electrical", "electric", "energy", "lighting", "power", "wiring", "generator"
            ],
            "Water and Sewer Infrastructure Services and Supplies": [
                "sewer", "water", "wastewater", "drainage", "pipe", "main", "rehabilitation", 
                "storm water", "sewage"
            ],
            "Vehicle Maintenance and Parts": [
                "vehicle", "truck", "car", "engine", "parts", "maintenance", "repair", "fleet",
                "automotive", "heavy rescue", "ladder"
            ],
            "IT - Software and Services": [
                "website", "software", "technology", "it ", "computer", "digital", "drupal", 
                "hosting", "development", "captioning"
            ],
            "Design and Engineering": [
                "design", "engineering", "architect", "planning", "consultant", "designer services"
            ],
            "Custodial Supplies and Services": [
                "custodial", "cleaning", "janitorial", "supplies", "sanitation"
            ],
            "Snow Removal and Salting/Sanding": [
                "snow", "ice", "salt", "sanding", "winter", "ice melt"
            ],
            "Food and Food Services": [
                "food", "meal", "catering", "kitchen", "dining", "breakfast", "lunch"
            ],
            "Transportation Services": [
                "transportation", "transit", "field trip", "bus", "transport"
            ],
            "Inspectional/Environmental Services": [
                "inspection", "environmental", "pest control", "rodent", "lead paint", "safety"
            ],
            "Rentals and Leasing, Equipment": [
                "rental", "lease", "equipment", "restroom rental", "lift"
            ],
            "Financial/Banking Services": [
                "financial", "banking", "accounting", "billing", "spending account", "fmla"
            ],
            "Printing, Marketing/Collateral Materials, Graphic Design": [
                "printing", "marketing", "graphic", "advertising", "collateral", "promotional"
            ],
            "Job-Related Training/Professional Memberships": [
                "training", "education", "professional", "membership", "development", "in service"
            ],
            "Vehicles/Heavy Equipment": [
                "heavy equipment", "machinery", "excavator", "heavy duty"
            ],
            "Community and Recreational Goods and Services": [
                "community", "recreational", "recreation", "center", "social"
            ]
        }
        
        # Check each category
        for industry, keywords in classification_rules.items():
            for keyword in keywords:
                if keyword in title_lower or keyword in dept_lower:
                    return industry
        
        # Special handling for DPW department
        if "dpw" in dept_lower:
            if any(word in title_lower for word in ["boiler", "hvac", "electrical"]):
                return "Energy and Electrical Services"
            elif any(word in title_lower for word in ["sewer", "water"]):
                return "Water and Sewer Infrastructure Services and Supplies"
            else:
                return "Construction (Public Works, Parks, Roadways)"
        
        # If no match found, return Other
        return "Other"
    
    # Apply industry classification to records missing it
    print("🏭 Applying industry classification...")
    mask = (df_combined['Industry'].isna()) | (df_combined['Industry'] == '') | (df_combined['Industry'] == 'Other')
    if mask.any():
        print(f"   Classifying {mask.sum()} contracts...")
        df_combined.loc[mask, 'Industry'] = df_combined.loc[mask].apply(
            lambda row: classify_industry(row.get('Title'), row.get('Department')), axis=1
        )
        
        # Show sample classifications
        newly_classified = df_combined.loc[mask, ['Title', 'Industry']].head(5)
        for _, row in newly_classified.iterrows():
            print(f"   📋 '{row['Title'][:50]}...' → {row['Industry']}")
    else:
        print("   ✅ All contracts already have industry classifications")

else:
    print("❌ No data collected from any scraper.")
    exit()

print("\n✅ All scrapers completed. Preview of combined data:")
print(df_combined.head(10))

# ----------------------------
# Upload to PostgreSQL
# ----------------------------
# Use DATABASE_URL environment variable for production, fallback to local for development
database_url = os.getenv('DATABASE_URL')

if database_url:
    # Production: Fix Heroku postgres URL for SQLAlchemy
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(database_url)
else:
    # Development: Use local database
    db_user = "scraper"
    db_password = "scraperpass"
    db_host = "localhost"
    db_port = "5432"
    db_name = "contracts"
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)

df_combined.to_sql("contract_opportunities", engine, if_exists="replace", index=False)
print("✅ Data uploaded to PostgreSQL")

# ----------------------------
# Upload to Google Sheets
# ----------------------------
try:
    import gspread
    from gspread_dataframe import set_with_dataframe
    from oauth2client.service_account import ServiceAccountCredentials
    
    # Get Google Sheets credentials from environment variable or file
    google_creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
    
    if google_creds_json:
        # Production: Use credentials from environment variable
        import tempfile
        creds_data = json.loads(google_creds_json)
        
        # Create temporary file for credentials
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(creds_data, temp_file)
            temp_creds_path = temp_file.name
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(temp_creds_path, scope)
        
        # Clean up temporary file
        os.unlink(temp_creds_path)
    else:
        # Development: Use local credentials file
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        CREDS_PATH = os.path.join(BASE_DIR, "google_sheets_credentials.json")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
    
    client = gspread.authorize(creds)
    spreadsheet = client.open("Contract Opportunities")
    worksheet = spreadsheet.sheet1
    worksheet.clear()
    set_with_dataframe(worksheet, df_combined)
    print("✅ Data uploaded to Google Sheets")
    
except Exception as e:
    print(f"⚠️ Google Sheets upload failed: {e}")
    print("✅ Data still saved to PostgreSQL database")
