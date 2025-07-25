import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

def clean_title(title):
    """
    Clean Somerville titles by removing IFB#, RFP# prefixes and numbers
    Examples:
    "RFP # 26-02 Water & Sewer Director & Inspectional Services Director Search" 
    -> "Water & Sewer Director & Inspectional Services Director Search"
    "IFB# 25-69 Supply & Delivery of Stone & Gravel" 
    -> "Supply & Delivery of Stone & Gravel"
    """
    if not title:
        return title
    
    # Remove IFB# or RFP# patterns with numbers
    # Patterns to match: "IFB# 25-69", "RFP # 26-02", "IFB #25-69", etc.
    cleaned = re.sub(r'^(IFB|RFP)\s*#?\s*[\d-]+\s*', '', title, flags=re.IGNORECASE)
    
    return cleaned.strip()

def scrape():
    url = "https://www.somervillema.gov/departments/finance/procurement-and-contracting-services"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # ----------------------------
    # Scrape the on-page table
    # ----------------------------
    table = soup.find("table")
    rows = []
    bid_page_urls = []  # Store individual bid page URLs
    
    if table:
        headers = [th.get_text(strip=True).replace("Sort ascending", "").strip() for th in table.find_all("th")]
        
        for tr in table.find_all("tr")[1:]:
            cells = []
            row_bid_url = None
            
            tds = tr.find_all("td")
            for i, td in enumerate(tds):
                cell_text = td.get_text(strip=True)
                cells.append(cell_text)
                
                # Check if this is the Title column (column index 1) and has a link
                if i == 1:  # Title column is the second column (index 1)
                    link = td.find("a", href=True)
                    if link:
                        href = link["href"]
                        # Make sure URL is absolute
                        if href.startswith("/"):
                            row_bid_url = "https://www.somervillema.gov" + href
                        elif href.startswith("http"):
                            row_bid_url = href
                        else:
                            row_bid_url = "https://www.somervillema.gov/" + href
            
            if cells:
                rows.append(cells)
                bid_page_urls.append(row_bid_url)
    
    df_web = pd.DataFrame(rows, columns=headers)
    # Add bid page URLs as a temporary column
    if bid_page_urls:
        df_web['_bid_page_url'] = bid_page_urls
    print("✅ On-page table scraped")
    print("df_web columns:", df_web.columns.tolist())

    # ----------------------------
    # Download Excel file
    # ----------------------------
    excel_url = None
    for link in soup.find_all("a", href=True):
        if ".xlsx" in link["href"]:
            excel_url = link["href"]
            break
    if excel_url and not excel_url.startswith("http"):
        excel_url = "https://www.somervillema.gov" + excel_url

    df_excel = pd.DataFrame()
    if excel_url:
        excel_response = requests.get(excel_url)
        with open("upcoming_bids.xlsx", "wb") as f:
            f.write(excel_response.content)
        df_excel = pd.read_excel("upcoming_bids.xlsx", skiprows=8)
        print("🔍 df_excel columns:", df_excel.columns.tolist())
        print("✅ Excel file downloaded and parsed")
    else:
        print("❌ Excel file not found")

    # ----------------------------
    # Normalize df_web
    # ----------------------------
    df_web_renamed = df_web.rename(columns={
        "Title": "Title",
        "Release Date": "Release Date",
        "Opening Date": "Due Date",
        "Instructions": "Instructions",
        "Bid Deposit": "Bid Deposit",
        "Addendum": "Addendum",
        "Bid Notice": "Document_PDF"  # Keep PDF info as separate field
    })

    # Clean titles by removing IFB#/RFP# prefixes
    if "Title" in df_web_renamed.columns:
        df_web_renamed["Title"] = df_web_renamed["Title"].apply(clean_title)
    
    df_web_renamed["Department"] = None
    df_web_renamed["Industry"] = None
    df_web_renamed["City"] = "Somerville"
    df_web_renamed["Estimated Value"] = None
    df_web_renamed["Source Type"] = "Open Bids"
    
    # Use the captured bid page URLs as Source URL
    if '_bid_page_url' in df_web.columns:
        df_web_renamed["Source URL"] = df_web['_bid_page_url']
    else:
        df_web_renamed["Source URL"] = None

    # Normalize df_excel
    if not df_excel.empty:
        df_excel_renamed = df_excel.rename(columns={
            "DESCRIPTION OF PURCHASE": "Title",
            "DEPARTMENT": "Department",
            "INDUSTRY TYPE": "Industry",
            "ESTIMATED TOTAL VALUE": "Estimated Value",
            "MONTH": "Month",
            "YEAR": "Year"
        })
        # Clean titles for Excel data too
        if "Title" in df_excel_renamed.columns:
            df_excel_renamed["Title"] = df_excel_renamed["Title"].apply(clean_title)
        
        df_excel_renamed["Release Date"] = df_excel_renamed["Month"].astype(str) + " " + df_excel_renamed["Year"].astype(str)
        df_excel_renamed["Due Date"] = None
        df_excel_renamed["Instructions"] = None
        df_excel_renamed["Bid Deposit"] = None
        df_excel_renamed["Addendum"] = None
        df_excel_renamed["City"] = "Somerville"
        df_excel_renamed["Source Type"] = "Upcoming Bids"
        df_excel_renamed["Source URL"] = url
        df_excel_renamed["Document_PDF"] = None  # Excel bids don't have PDF documents
    else:
        df_excel_renamed = pd.DataFrame(columns=df_web_renamed.columns)

    # ----------------------------
    # Final formatting
    # ----------------------------
    columns = [
        "Title", "Department", "Industry", "Estimated Value",
        "Release Date", "Due Date", "Instructions", "Bid Deposit",
        "Addendum", "City", "Source Type", "Source URL", "Document_PDF"
    ]
    df_web_clean = df_web_renamed[columns]
    df_excel_clean = df_excel_renamed[columns]

    df_combined = pd.concat([df_web_clean, df_excel_clean], ignore_index=True)

    # Add status
    def determine_status(due_date_str):
        if pd.isna(due_date_str) or due_date_str.strip() == "":
            return "Upcoming"
        try:
            # Handle format with day of week: "Wed, 07/09/2025 - 12:00pm"
            if ", " in due_date_str and " - " in due_date_str:
                # Extract just the date and time part, removing day of week
                date_time_part = due_date_str.split(", ", 1)[1]  # Gets "07/09/2025 - 12:00pm"
                due = datetime.strptime(date_time_part, "%m/%d/%Y - %I:%M%p")
            else:
                # Original format: "07/09/2025 - 12:00pm"
                due = datetime.strptime(due_date_str, "%m/%d/%Y - %I:%M%p")
            return "Open" if due > datetime.now() else "Closed"
        except ValueError:
            try:
                # Try alternative formats
                if ", " in due_date_str:
                    date_time_part = due_date_str.split(", ", 1)[1]
                    # Handle lowercase am/pm: "12:00pm"
                    due = datetime.strptime(date_time_part, "%m/%d/%Y - %I:%M%p")
                else:
                    due = datetime.strptime(due_date_str, "%m/%d/%Y - %I:%M%p")
                return "Open" if due > datetime.now() else "Closed"
            except ValueError:
                return "Open"

    df_combined["status"] = df_combined["Due Date"].apply(determine_status)

    return df_combined
