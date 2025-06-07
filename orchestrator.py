# TODOs
# - Support downloading and saving bid documents (e.g. PDFs)
# - Normalize messy text fields like 'Title', but retain original raw fields

from scrapers import somerville
from scrapers.cambridge import scrape as scrape_cambridge
import pandas as pd
from sqlalchemy import create_engine

# ----------------------------
# Run all scrapers
# ----------------------------
df_somerville = somerville.scrape()
df_cambridge = scrape_cambridge()
print("🔍 Cambridge rows scraped:", len(df_cambridge))

# Combine safely
dfs = [df for df in [df_somerville, df_cambridge] if not df.empty]
if dfs:
    df_combined = pd.concat(dfs, ignore_index=True)
else:
    print("❌ No data collected from any scraper.")
    exit()

print("\n✅ All scrapers completed. Preview of combined data:")
print(df_combined.head(10))

# ----------------------------
# Upload to PostgreSQL
# ----------------------------
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
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_sheets_credentials.json", scope)
client = gspread.authorize(creds)

spreadsheet = client.open("Contract Opportunities")
worksheet = spreadsheet.sheet1
worksheet.clear()
set_with_dataframe(worksheet, df_combined)
print("✅ Data uploaded to Google Sheets")

