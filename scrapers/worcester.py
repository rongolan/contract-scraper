import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import time

def scrape():
    """
    Enhanced Worcester scraper using two-step approach:
    1. Scrape main table for basic info and individual bid URLs
    2. Scrape each individual bid page for detailed information
    Returns DataFrame with comprehensive bid data
    """
    base_url = "http://www.worcesterma.gov"
    main_url = f"{base_url}/finance/purchasing-bids/bids/open-bids"
    
    print("🔍 Scraping Worcester main bid table...")
    
    # Step 1: Scrape main table
    try:
        response = requests.get(main_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error fetching Worcester main page: {e}")
        return pd.DataFrame()
    
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")
    if not table:
        print("❌ No table found on Worcester bids page")
        return pd.DataFrame()
    
    rows = []
    table_rows = table.find_all("tr")
    
    # Process each bid from the table
    for i, tr in enumerate(table_rows[1:], 1):  # Skip header
        cells = tr.find_all("td")
        if len(cells) >= 3:
            # Extract basic info from table
            bid_number_cell = cells[0]
            title_cell = cells[1]
            close_date = cells[2].get_text(strip=True)
            
            bid_number = bid_number_cell.get_text(strip=True)
            title = title_cell.get_text(strip=True)
            
            # Extract individual bid page URL from bid number link
            individual_bid_url = None
            link = bid_number_cell.find("a", href=True)
            if link:
                href = link["href"]
                if href.startswith("http"):
                    individual_bid_url = href
                elif href.startswith("/"):
                    individual_bid_url = base_url + href
                else:
                    individual_bid_url = f"{base_url}/{href}"
            
            # Start with basic data from table
            row_data = {
                "Title": title,
                "Department": extract_department(title),
                "Industry": None,
                "Estimated Value": None,
                "Release Date": None,
                "Due Date": standardize_close_date(close_date),
                "Instructions": None,
                "Bid Deposit": None,
                "Addendum": None,
                "Comments": None,
                "Standard_Forms": None,
                "Bid_Forms": None,
                "City": "Worcester",
                "Source Type": "Open Bids",
                "Source URL": individual_bid_url or main_url,
                "Bid Number": bid_number,
                "status": determine_status(close_date)
            }
            
            # Step 2: Scrape individual bid page for detailed info
            if individual_bid_url:
                print(f"   📄 Scraping individual bid {i}: {bid_number}")
                enhanced_data = scrape_individual_bid(individual_bid_url)
                if enhanced_data:
                    # Update row_data with enhanced information
                    row_data.update(enhanced_data)
                
                # Rate limiting: delay between requests
                time.sleep(1.5)  # 1.5 second delay to be respectful
            
            rows.append(row_data)
    
    if not rows:
        print("⚠️ No bid data found in Worcester table")
        return pd.DataFrame()
    
    df = pd.DataFrame(rows, columns=[
        "Title", "Department", "Industry", "Estimated Value", "Release Date",
        "Due Date", "Instructions", "Bid Deposit", "Addendum", "Comments",
        "Standard_Forms", "Bid_Forms", "City", "Source Type", "Source URL", 
        "Bid Number", "status"
    ])
    
    print(f"✅ Worcester enhanced scraping complete: {len(df)} bids with detailed data")
    return df

def scrape_individual_bid(bid_url):
    """
    Scrape individual Worcester bid page for detailed information
    Returns dict with enhanced bid data or None if scraping fails
    """
    try:
        response = requests.get(bid_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        enhanced_data = {}
        
        # Extract Industry
        industry_element = soup.find(string=re.compile(r"Industry|Category"))
        if industry_element:
            # Look for the industry value near the label
            parent = industry_element.parent
            if parent:
                industry_text = parent.get_text()
                # Extract industry from text like "Industry: Environmental Services"
                industry_match = re.search(r"(?:Industry|Category):\s*(.+)", industry_text)
                if industry_match:
                    enhanced_data["Industry"] = industry_match.group(1).strip()
        
        # Extract Open Date
        open_date_element = soup.find(string=re.compile(r"Open Date|Issue Date|Posted"))
        if open_date_element:
            parent = open_date_element.parent
            if parent:
                date_text = parent.get_text()
                date_match = re.search(r"(\d{2}/\d{2}/\d{4})", date_text)
                if date_match:
                    enhanced_data["Release Date"] = standardize_date(date_match.group(1))
        
        # Extract Comments/Description
        comments_element = soup.find(string=re.compile(r"Comments|Description|Details"))
        if comments_element:
            parent = comments_element.parent
            if parent:
                # Get the text content and clean it up
                comments_text = parent.get_text(strip=True)
                # Remove the label part
                comments_text = re.sub(r"^(Comments|Description|Details):\s*", "", comments_text)
                if comments_text and len(comments_text) > 10:  # Only if substantial content
                    enhanced_data["Comments"] = comments_text[:500]  # Limit length
        
        # Extract Standard Forms
        standard_forms = []
        for form_text in ["CORI", "EPP", "MWBE", "REAP", "Wage Theft"]:
            if soup.find(string=re.compile(form_text, re.IGNORECASE)):
                standard_forms.append(form_text)
        if standard_forms:
            enhanced_data["Standard_Forms"] = ", ".join(standard_forms)
        
        # Extract Bid-Specific Forms
        bid_forms = []
        # Look for links to documents/forms
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            link_text = link.get_text(strip=True)
            if any(ext in href.lower() for ext in [".pdf", ".doc", ".xls"]):
                if any(word in link_text.lower() for word in ["form", "spec", "drawing", "addendum"]):
                    bid_forms.append(link_text)
        if bid_forms:
            enhanced_data["Bid_Forms"] = ", ".join(bid_forms[:5])  # Limit to 5 forms
        
        return enhanced_data
        
    except Exception as e:
        print(f"   ⚠️ Failed to scrape individual bid page {bid_url}: {e}")
        return None  # Return None so we keep basic table data

def extract_department(title):
    """
    Extract department from title if present (e.g., "Project Name / DPW" -> "DPW")
    """
    if " / " in title:
        parts = title.split(" / ")
        if len(parts) > 1:
            return parts[-1].strip()
    return None

def standardize_close_date(date_str):
    """
    Standardize Worcester's close date format
    Expected format: "07/15/2025 - 04:00 PM"
    """
    if not date_str or date_str.strip() == "":
        return None
    
    date_str = date_str.strip()
    
    # Try to parse Worcester's expected format: MM/DD/YYYY - HH:MM PM
    try:
        # Handle formats like "07/15/2025 - 04:00 PM"
        if " - " in date_str:
            date_part, time_part = date_str.split(" - ", 1)
            
            # Parse date part
            date_obj = datetime.strptime(date_part.strip(), "%m/%d/%Y")
            
            # Parse time part
            time_part = time_part.strip()
            time_obj = datetime.strptime(time_part, "%I:%M %p")
            
            # Combine date and time
            combined = datetime.combine(date_obj.date(), time_obj.time())
            return combined.strftime("%Y-%m-%d %I:%M %p")
        
        # Fallback: try just date format
        else:
            date_obj = datetime.strptime(date_str, "%m/%d/%Y")
            return date_obj.strftime("%Y-%m-%d")
            
    except ValueError:
        # If parsing fails, return the original string
        print(f"⚠️ Could not parse Worcester date: '{date_str}'")
        return date_str

def determine_status(close_date_str):
    """
    Determine if bid is open, upcoming, or closed based on close date
    """
    if not close_date_str:
        return "Open"
    
    try:
        # Parse the close date to compare with current time
        if " - " in close_date_str:
            date_part = close_date_str.split(" - ")[0].strip()
            close_date = datetime.strptime(date_part, "%m/%d/%Y")
        else:
            close_date = datetime.strptime(close_date_str.strip(), "%m/%d/%Y")
        
        now = datetime.now()
        if close_date < now:
            return "Closed"
        else:
            return "Open"
    except ValueError:
        return "Open"  # Default to open if we can't parse the date

if __name__ == "__main__":
    df = scrape()
    if not df.empty:
        print("\nWorcester bid data:")
        print(df[['Title', 'Due Date', 'Bid Number', 'status']].head())
    else:
        print("No data retrieved")