import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import time

def scrape():
    """
    Enhanced Quincy scraper using two-step approach:
    1. Scrape main table for basic info and individual bid URLs
    2. Scrape each individual bid page for detailed information (with fallback)
    Returns DataFrame with comprehensive bid data
    """
    base_url = "https://www.quincyma.gov"
    main_url = f"{base_url}/departments/purchasing/current_bids.php"
    
    print("🔍 Scraping Quincy main bid table...")
    
    # Step 1: Scrape main table
    try:
        response = requests.get(main_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error fetching Quincy main page: {e}")
        return pd.DataFrame()
    
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find bid links using a more targeted approach
    bid_links = soup.find_all("a", href=re.compile(r"bid_detail_.*\.php"))
    
    if not bid_links:
        print("❌ No bid detail links found on Quincy page")
        return pd.DataFrame()
    
    rows = []
    page_text = soup.get_text()
    lines = [line.strip() for line in page_text.split('\n') if line.strip()]
    
    # Process each unique bid
    processed_urls = set()  # Track processed URLs to avoid duplicates
    
    for i, bid_link in enumerate(bid_links, 1):
        individual_bid_url = bid_link.get("href")
        
        # Skip if we've already processed this URL
        if individual_bid_url in processed_urls:
            continue
        processed_urls.add(individual_bid_url)
        
        title = bid_link.get_text(strip=True)
        
        # Make URL absolute
        if individual_bid_url and not individual_bid_url.startswith("http"):
            if individual_bid_url.startswith("/"):
                individual_bid_url = base_url + individual_bid_url
            else:
                individual_bid_url = f"{base_url}/{individual_bid_url}"
        
        # Extract dates from surrounding text
        issue_date = None
        due_date = None
        
        # Find the context around this bid title in the page text
        title_context = extract_bid_context(lines, title)
        if title_context:
            issue_date, due_date = parse_bid_dates_from_context(title_context)
            
            # Start with basic data from table
            row_data = {
                "Title": title,
                "Department": extract_department(title),
                "Industry": classify_industry(title),
                "Estimated Value": None,
                "Release Date": issue_date,
                "Due Date": due_date,
                "Instructions": None,
                "Bid Deposit": None,
                "Addendum": None,
                "Comments": None,
                "Standard_Forms": None,
                "Bid_Forms": None,
                "City": "Quincy",
                "Source Type": "Current Bids",
                "Source URL": individual_bid_url or main_url,
                "Bid Number": extract_bid_number(title),
                "status": determine_status(due_date)
            }
            
            # Step 2: Attempt to scrape individual bid page for detailed info
            if individual_bid_url:
                print(f"   📄 Attempting to scrape individual bid {i}: {title}")
                enhanced_data = scrape_individual_bid(individual_bid_url)
                if enhanced_data:
                    # Update row_data with enhanced information
                    row_data.update(enhanced_data)
                    print(f"   ✅ Enhanced data retrieved for: {title}")
                else:
                    print(f"   ⚠️ Could not access individual page, using table data for: {title}")
                
                # Rate limiting: delay between requests
                time.sleep(1.5)  # 1.5 second delay to be respectful
            
            rows.append(row_data)
    
    if not rows:
        print("⚠️ No bid data found in Quincy table")
        return pd.DataFrame()
    
    df = pd.DataFrame(rows, columns=[
        "Title", "Department", "Industry", "Estimated Value", "Release Date",
        "Due Date", "Instructions", "Bid Deposit", "Addendum", "Comments",
        "Standard_Forms", "Bid_Forms", "City", "Source Type", "Source URL", 
        "Bid Number", "status"
    ])
    
    print(f"✅ Quincy enhanced scraping complete: {len(df)} bids with detailed data")
    return df

def scrape_individual_bid(bid_url):
    """
    Scrape individual Quincy bid page for detailed information
    Returns dict with enhanced bid data or None if scraping fails
    """
    try:
        response = requests.get(bid_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        enhanced_data = {}
        
        # Extract estimated value
        value_patterns = [
            r"\$[\d,]+(?:\.\d{2})?",
            r"estimate[d]?\s*[:\-]\s*\$?[\d,]+",
            r"budget[:\-]\s*\$?[\d,]+",
            r"value[:\-]\s*\$?[\d,]+"
        ]
        
        page_text = soup.get_text()
        for pattern in value_patterns:
            value_match = re.search(pattern, page_text, re.IGNORECASE)
            if value_match:
                enhanced_data["Estimated Value"] = value_match.group(0)
                break
        
        # Extract detailed description/comments
        # Look for content areas that might contain descriptions
        content_areas = soup.find_all(['div', 'p'], class_=re.compile(r'content|description|detail'))
        for area in content_areas:
            text = area.get_text(strip=True)
            if len(text) > 50:  # Only substantial content
                enhanced_data["Comments"] = text[:500]  # Limit length
                break
        
        # Extract instructions
        instruction_element = soup.find(string=re.compile(r"instruction|requirement|specification", re.IGNORECASE))
        if instruction_element:
            parent = instruction_element.parent
            if parent:
                instructions_text = parent.get_text(strip=True)
                enhanced_data["Instructions"] = instructions_text[:300]
        
        # Extract bid deposit information
        deposit_element = soup.find(string=re.compile(r"deposit|bond", re.IGNORECASE))
        if deposit_element:
            parent = deposit_element.parent
            if parent:
                deposit_text = parent.get_text(strip=True)
                enhanced_data["Bid Deposit"] = deposit_text[:200]
        
        # Look for addendum information
        addendum_element = soup.find(string=re.compile(r"addendum|amendment", re.IGNORECASE))
        if addendum_element:
            enhanced_data["Addendum"] = "Addendum Available"
        
        # Check for standard forms
        standard_forms = []
        form_keywords = ["CORI", "EPP", "MWBE", "Wage Theft", "Prevailing Wage", "Union"]
        for keyword in form_keywords:
            if soup.find(string=re.compile(keyword, re.IGNORECASE)):
                standard_forms.append(keyword)
        
        if standard_forms:
            enhanced_data["Standard_Forms"] = ", ".join(standard_forms)
        
        return enhanced_data
        
    except requests.RequestException as e:
        print(f"   ⚠️ Could not access individual bid page: {e}")
        return None
    except Exception as e:
        print(f"   ⚠️ Error parsing individual bid page: {e}")
        return None

def parse_quincy_date(date_text):
    """
    Parse Quincy date format (e.g., "July 23, 2025") to YYYY-MM-DD
    """
    if not date_text:
        return None
    
    try:
        # Handle "Month DD, YYYY" format
        date_match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})", date_text)
        if date_match:
            month_name = date_match.group(1)
            day = date_match.group(2)
            year = date_match.group(3)
            return convert_month_name_to_date(month_name, day, year)
        
        # Handle MM/DD/YYYY format as fallback
        date_obj = datetime.strptime(date_text.strip(), "%m/%d/%Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        print(f"⚠️ Could not parse Quincy date: '{date_text}'")
        return None

def parse_quincy_date_with_time(date_text):
    """
    Parse Quincy date with time format (e.g., "August 07, 2025 11:00 AM") to YYYY-MM-DD H:MM AM/PM
    """
    if not date_text:
        return None
    
    try:
        # Handle "Month DD, YYYY H:MM AM/PM" format
        datetime_match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})\s+(\d{1,2}:\d{2}\s+[AP]M)", date_text)
        if datetime_match:
            month_name = datetime_match.group(1)
            day = datetime_match.group(2)
            year = datetime_match.group(3)
            time_part = datetime_match.group(4)
            return convert_month_name_to_date_with_time(month_name, day, year, time_part)
        
        # Fallback: just extract date part
        return parse_quincy_date(date_text)
    except ValueError:
        print(f"⚠️ Could not parse Quincy date/time: '{date_text}'")
        return parse_quincy_date(date_text)

def extract_bid_context(lines, title):
    """
    Extract the context lines around a bid title for date parsing
    """
    context_lines = []
    title_found = False
    
    for i, line in enumerate(lines):
        if title in line:
            title_found = True
            # Get the current line and next few lines
            context_lines.extend(lines[i:i+4])
            break
    
    return context_lines if title_found else []

def parse_bid_dates_from_context(context_lines):
    """
    Parse issue date and due date from context lines
    Returns tuple: (issue_date, due_date)
    """
    issue_date = None
    due_date = None
    
    for line in context_lines:
        # Look for date patterns in "Month DD, YYYY" format
        date_match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})", line)
        if date_match:
            month_name = date_match.group(1)
            day = date_match.group(2)
            year = date_match.group(3)
            
            # Check if this line also contains time (indicating due date)
            time_match = re.search(r"(\d{1,2}:\d{2}\s+[AP]M)", line)
            if time_match:
                time_part = time_match.group(1)
                due_date = convert_month_name_to_date_with_time(month_name, day, year, time_part)
            else:
                # First date without time is likely issue date
                if not issue_date:
                    issue_date = convert_month_name_to_date(month_name, day, year)
                # Second date without time could be due date
                elif not due_date:
                    due_date = convert_month_name_to_date(month_name, day, year)
    
    return issue_date, due_date


def convert_month_name_to_date(month_name, day, year):
    """
    Convert month name format to YYYY-MM-DD
    """
    try:
        date_str = f"{month_name} {day}, {year}"
        date_obj = datetime.strptime(date_str, "%B %d, %Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        print(f"⚠️ Could not parse date: {month_name} {day}, {year}")
        return None

def convert_month_name_to_date_with_time(month_name, day, year, time_part):
    """
    Convert month name format with time to YYYY-MM-DD H:MM AM/PM
    """
    try:
        date_str = f"{month_name} {day}, {year}"
        date_obj = datetime.strptime(date_str, "%B %d, %Y")
        
        # Parse time part
        time_obj = datetime.strptime(time_part, "%I:%M %p")
        
        # Combine date and time
        combined = datetime.combine(date_obj.date(), time_obj.time())
        return combined.strftime("%Y-%m-%d %I:%M %p")
    except ValueError:
        print(f"⚠️ Could not parse date/time: {month_name} {day}, {year} {time_part}")
        return convert_month_name_to_date(month_name, day, year)

def classify_industry(title):
    """
    Basic industry classification based on title keywords
    """
    title_lower = title.lower()
    
    # Define industry keywords
    industry_map = {
        "Security": ["security", "surveillance", "guard"],
        "Vehicle/Fleet": ["vehicle", "truck", "car", "suv", "fleet", "ford", "chevrolet", "toyota"],
        "Construction": ["construction", "building", "renovation", "concrete", "paving"],
        "IT/Technology": ["software", "computer", "technology", "IT", "system", "network"],
        "Landscaping": ["landscaping", "lawn", "tree", "grounds", "maintenance"],
        "Professional Services": ["consulting", "legal", "accounting", "audit", "professional"],
        "Utilities": ["water", "sewer", "electric", "utility", "pump"],
        "Waste Management": ["waste", "trash", "garbage", "recycling"],
        "Food Services": ["food", "catering", "meal", "kitchen"],
        "Medical/Health": ["medical", "health", "hospital", "clinic"],
        "Education": ["education", "school", "training", "learning"],
        "Emergency Services": ["emergency", "fire", "police", "ambulance"],
        "Maintenance": ["maintenance", "repair", "service", "cleaning"]
    }
    
    for industry, keywords in industry_map.items():
        if any(keyword in title_lower for keyword in keywords):
            return industry
    
    return "General Services"

def extract_department(title):
    """
    Extract department from title if present
    """
    # Look for common department patterns
    dept_patterns = [
        r"\b(DPW|Public Works|Police|Fire|Parks|Recreation|Engineering|IT|Finance|Purchasing)\b",
        r"\b(Water|Sewer|Highway|Building|Planning|Health)\b"
    ]
    
    for pattern in dept_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def extract_bid_number(title):
    """
    Extract bid number from title if present
    """
    # Look for bid number patterns
    patterns = [
        r"#(\w+[-\w]*)",
        r"Bid\s*(\w+[-\w]*)",
        r"RFP\s*(\w+[-\w]*)",
        r"IFB\s*(\w+[-\w]*)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def standardize_date(date_str):
    """
    Standardize date from M/D/YYYY or MM/DD/YYYY to YYYY-MM-DD format
    """
    if not date_str:
        return None
        
    try:
        # Handle formats like "12/15/2024" or "1/5/2024"
        date_obj = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        try:
            # Try with different separators
            date_str_clean = date_str.strip().replace("-", "/").replace(".", "/")
            date_obj = datetime.strptime(date_str_clean, "%m/%d/%Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            print(f"⚠️ Could not parse Quincy date: '{date_str}'")
            return date_str

def standardize_date_with_time(date_str, time_str):
    """
    Standardize date and time to YYYY-MM-DD H:MM AM/PM format
    """
    if not date_str or not time_str:
        return standardize_date(date_str)
    
    try:
        # Parse date part
        date_obj = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        
        # Parse time part
        time_str_clean = time_str.strip().upper()
        time_obj = datetime.strptime(time_str_clean, "%I:%M %p")
        
        # Combine date and time
        combined = datetime.combine(date_obj.date(), time_obj.time())
        return combined.strftime("%Y-%m-%d %I:%M %p")
        
    except ValueError:
        print(f"⚠️ Could not parse Quincy date/time: '{date_str}' / '{time_str}'")
        return standardize_date(date_str)

def determine_status(due_date_str):
    """
    Determine if bid is open, upcoming, or closed based on due date
    """
    if not due_date_str:
        return "Open"
    
    try:
        # Parse the due date to compare with current time
        if " " in due_date_str:  # Has time component
            date_part = due_date_str.split(" ")[0]
        else:
            date_part = due_date_str
            
        due_date = datetime.strptime(date_part, "%Y-%m-%d")
        now = datetime.now()
        
        if due_date < now:
            return "Closed"
        else:
            return "Open"
    except ValueError:
        return "Open"  # Default to open if we can't parse the date

if __name__ == "__main__":
    df = scrape()
    if not df.empty:
        print("\nQuincy bid data:")
        for idx, row in df.iterrows():
            print(f"Bid {idx + 1}:")
            print(f"  Title: {row['Title']}")
            print(f"  Release Date: {row['Release Date']}")
            print(f"  Due Date: {row['Due Date']}")
            print(f"  Industry: {row['Industry']}")
            print(f"  Status: {row['status']}")
            print()
    else:
        print("No data retrieved")