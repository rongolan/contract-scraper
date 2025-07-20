import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import time

def scrape():
    """
    Enhanced Boston scraper using two-step approach:
    1. Scrape main bid listings for basic info and individual bid URLs (all pages)
    2. Scrape each individual bid page for detailed information
    Returns DataFrame with comprehensive bid data
    """
    base_url = "https://www.boston.gov"
    main_url = f"{base_url}/bid-listings"
    
    print("🔍 Scraping Boston main bid listings...")
    
    rows = []
    page = 1
    
    while True:
        # Build page URL (first page has no ?page= parameter)
        if page == 1:
            page_url = main_url
        else:
            page_url = f"{main_url}?page={page}"
        
        print(f"   📄 Scraping page {page}...")
        
        # Step 1: Scrape current page of bid listings
        try:
            response = requests.get(page_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Error fetching Boston page {page}: {e}")
            break
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find bid containers using the correct structure from page source
        # Each bid is in a div.views-row container
        bid_containers = soup.find_all("div", class_="views-row")
        
        # Filter to only containers that actually contain bid links (not empty rows)
        actual_bid_containers = []
        for container in bid_containers:
            # Check if this container has a bid link (href contains /bid-listings/)
            bid_link = container.find("a", href=True)
            if bid_link and "/bid-listings/" in bid_link.get("href", ""):
                actual_bid_containers.append(container)
        
        if not actual_bid_containers:
            # Debug: show what we actually found
            print(f"   🔍 Debug: Found {len(bid_containers)} views-row containers, but 0 actual bid containers")
            if page == 1:
                print("   🔍 Debug: Sample containers found:")
                for container in bid_containers[:3]:
                    link = container.find("a", href=True)
                    link_info = f"{link.get_text()[:30]} -> {link.get('href')}" if link else "No link"
                    print(f"      - Container: {link_info}")
            print(f"   ✅ No more bids found on page {page} - pagination complete")
            break
        
        bid_containers = actual_bid_containers
        
        print(f"   📋 Found {len(bid_containers)} bids on page {page}")
        page_rows = []
    
        # Process each bid from current page
        for i, container in enumerate(bid_containers, 1):
            # Extract basic info from listing
            title_link = container.find("a")
            if not title_link:
                continue
                
            title = title_link.get_text(strip=True)
            individual_bid_url = title_link.get("href")
            
            # Make URL absolute
            if individual_bid_url and individual_bid_url.startswith("/"):
                individual_bid_url = base_url + individual_bid_url
            
            # Extract other basic info from listing
            date_info = container.find("div", class_="txt")
            posted_date = None
            due_date = None
            
            if date_info:
                date_text = date_info.get_text()
                # Look for "Posted" and "Due" dates
                posted_match = re.search(r"Posted:\s*([^|]+)", date_text)
                due_match = re.search(r"Due:\s*([^|]+)", date_text)
                
                if posted_match:
                    posted_date = standardize_date(posted_match.group(1).strip())
                if due_match:
                    due_date = standardize_date(due_match.group(1).strip())
            
            # Extract department if shown
            department = extract_department_from_listing(container)
            
            # Start with basic data from listing
            row_data = {
                "Title": title,
                "Department": department,
                "Industry": None,
                "Estimated Value": None,
                "Release Date": posted_date,
                "Due Date": due_date,
                "Instructions": None,
                "Bid Deposit": None,
                "Addendum": None,
                "Comments": None,
                "Standard_Forms": None,
                "Bid_Forms": None,
                "City": "Boston",
                "Source Type": "Open Bids",
                "Source URL": individual_bid_url or page_url,
                "Bid Number": extract_bid_number(title),
                "status": determine_status(due_date)
            }
            
            # Step 2: Scrape individual bid page for detailed info
            if individual_bid_url:
                bid_number = f"Page {page}, Bid {i}"
                print(f"      📄 Scraping individual bid {bid_number}: {title[:30]}...")
                enhanced_data = scrape_individual_bid(individual_bid_url)
                if enhanced_data:
                    # Update row_data with enhanced information
                    row_data.update(enhanced_data)
                
                # Rate limiting: delay between requests
                time.sleep(1.5)  # 1.5 second delay to be respectful
            
            page_rows.append(row_data)
        
        # Add page rows to main rows list
        rows.extend(page_rows)
        
        # Check if there are more pages by looking for pagination links
        # Boston uses links with ?page=X in href and titles like "Go to page X" or "Go to next page"
        all_page_links = soup.find_all("a", href=True)
        has_next_page = False
        
        for link in all_page_links:
            href = link.get("href", "")
            title = link.get("title", "")
            text = link.get_text()
            
            # Look for next page links in various formats
            if (("?page=" in href) and 
                (f"page={page}" in href or 
                 "next page" in title.lower() or 
                 "››" in text or
                 f"page {page + 1}" in title.lower())):
                has_next_page = True
                print(f"   🔍 Found next page link: {title} -> {href}")
                break
        
        if not has_next_page:
            print(f"   ✅ No next page found - pagination complete")
            break
            
        page += 1
        
        # Rate limiting between pages
        time.sleep(2)
    
    if not rows:
        print("⚠️ No bid data found in Boston listings")
        return pd.DataFrame()
    
    df = pd.DataFrame(rows, columns=[
        "Title", "Department", "Industry", "Estimated Value", "Release Date",
        "Due Date", "Instructions", "Bid Deposit", "Addendum", "Comments",
        "Standard_Forms", "Bid_Forms", "City", "Source Type", "Source URL", 
        "Bid Number", "status"
    ])
    
    print(f"✅ Boston enhanced scraping complete: {len(df)} bids with detailed data")
    return df

def scrape_individual_bid(bid_url):
    """
    Scrape individual Boston bid page for detailed information using Boston-specific field mapping
    Returns dict with enhanced bid data or None if scraping fails
    """
    try:
        response = requests.get(bid_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        enhanced_data = {}
        content_text = soup.get_text()
        
        # Extract Industry using Boston-specific Type + UNSPSC + content analysis
        industry = extract_boston_industry(soup, content_text)
        if industry:
            enhanced_data["Industry"] = industry
        
        # Extract Estimated Value - Boston specific patterns
        estimated_value = extract_boston_estimated_value(content_text)
        if estimated_value:
            enhanced_data["Estimated Value"] = estimated_value
        
        # Extract Release Date - look for "RFQ Available", "Posted", etc.
        release_date = extract_boston_release_date(content_text)
        if release_date:
            enhanced_data["Release Date"] = release_date
        
        # Extract Due Date - look for "SOQ Submission Deadline", "Due", etc.
        due_date = extract_boston_due_date(content_text)
        if due_date:
            enhanced_data["Due Date"] = due_date
        
        # Extract Comments - project description + location
        comments = extract_boston_comments(soup, content_text)
        if comments:
            enhanced_data["Comments"] = comments[:500]  # Limit length
        
        # Extract Instructions - Boston submission requirements
        instructions = extract_boston_instructions(content_text)
        if instructions:
            enhanced_data["Instructions"] = instructions[:300]
        
        # Extract Standard Forms - Boston specific requirements
        standard_forms = extract_boston_standard_forms(content_text)
        if standard_forms:
            enhanced_data["Standard_Forms"] = standard_forms
        
        # Extract Bid-Specific Forms/Documents
        bid_forms = extract_boston_bid_forms(soup)
        if bid_forms:
            enhanced_data["Bid_Forms"] = bid_forms
        
        return enhanced_data
        
    except Exception as e:
        print(f"   ⚠️ Failed to scrape individual bid page {bid_url}: {e}")
        return None  # Return None so we keep basic listing data

def extract_department_from_listing(container):
    """
    Extract department from bid listing container
    """
    # Look for department indicators in the container
    dept_indicators = container.find_all("img", alt=True)
    for img in dept_indicators:
        alt_text = img.get("alt", "")
        if "department" in alt_text.lower() or "dept" in alt_text.lower():
            return alt_text
    
    # Fallback: look for department in text
    text = container.get_text()
    dept_match = re.search(r"Department:\s*([^\n]+)", text, re.IGNORECASE)
    if dept_match:
        return dept_match.group(1).strip()
    
    return None

def extract_bid_number(title):
    """
    Extract bid number from title if present
    """
    # Look for patterns like "RFP-2025-123", "IFB 25-456", etc.
    bid_patterns = [
        r"(RFP[-\s]*\d{2,4}[-\s]*\d+)",
        r"(IFB[-\s]*\d{2,4}[-\s]*\d+)",
        r"(RFS[-\s]*\d{2,4}[-\s]*\d+)",
        r"(\d{4}[-\s]*\d+)"
    ]
    
    for pattern in bid_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def extract_boston_industry(soup, content_text):
    """
    Extract industry classification using Boston-specific Type + UNSPSC + content analysis
    """
    # Extract Type field (Paper, Electronic, etc.)
    type_match = re.search(r"Type:\s*(\w+)", content_text, re.IGNORECASE)
    bid_type = type_match.group(1) if type_match else None
    
    # Extract UNSPSC code
    unspsc_match = re.search(r"UNSPSC[:\s]*(\d+)", content_text, re.IGNORECASE)
    unspsc_code = unspsc_match.group(1) if unspsc_match else None
    
    # Map UNSPSC codes to industries (basic mapping for now)
    if unspsc_code:
        unspsc_prefix = unspsc_code[:2] if len(unspsc_code) >= 2 else ""
        if unspsc_prefix == "72":  # Construction and building
            return "Construction (Buildings)"
        elif unspsc_prefix == "93":  # Professional services
            return "Design and Engineering"
        elif unspsc_prefix == "81":  # Information technology
            return "IT - Software and Services"
    
    # Fallback to content analysis
    content_lower = content_text.lower()
    if any(word in content_lower for word in ["construction", "building", "community center", "renovation"]):
        return "Construction (Buildings)"
    elif any(word in content_lower for word in ["fiscal agent", "financial", "professional services"]):
        return "Design and Engineering"
    elif any(word in content_lower for word in ["software", "technology", "digital", "monitoring"]):
        return "IT - Software and Services"
    elif any(word in content_lower for word in ["vehicle", "boat", "equipment", "repair"]):
        return "Vehicle Maintenance and Parts"
    elif any(word in content_lower for word in ["tree", "planting", "park", "playground"]):
        return "Construction (Public Works, Parks, Roadways)"
    
    return "Other"

def extract_boston_estimated_value(content_text):
    """
    Extract estimated value using Boston-specific patterns
    """
    # Look for "Estimated Construction Cost: $50,000,000"
    construction_cost_match = re.search(r"Estimated Construction Cost[:\s]*\$?([\d,]+)", content_text, re.IGNORECASE)
    if construction_cost_match:
        return f"${construction_cost_match.group(1)}"
    
    # Look for other budget patterns
    budget_patterns = [
        r"Budget[:\s]*\$?([\d,]+)",
        r"Value[:\s]*\$?([\d,]+)",
        r"Amount[:\s]*\$?([\d,]+)"
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, content_text, re.IGNORECASE)
        if match:
            return f"${match.group(1)}"
    
    return None

def extract_boston_release_date(content_text):
    """
    Extract release date using Boston-specific patterns
    """
    # Look for "RFQ Available: July 7, 2025"
    rfq_match = re.search(r"RFQ Available[:\s]*([A-Za-z]+ \d{1,2}, \d{4})", content_text, re.IGNORECASE)
    if rfq_match:
        return standardize_date(rfq_match.group(1))
    
    # Look for "Posted: 07/07/2025"
    posted_match = re.search(r"Posted[:\s]*(\d{1,2}/\d{1,2}/\d{4})", content_text, re.IGNORECASE)
    if posted_match:
        return standardize_date(posted_match.group(1))
    
    return None

def extract_boston_due_date(content_text):
    """
    Extract due date using Boston-specific patterns
    """
    # Look for "SOQ Submission Deadline: July 22, 2025"
    soq_match = re.search(r"SOQ Submission Deadline[:\s]*([A-Za-z]+ \d{1,2}, \d{4})", content_text, re.IGNORECASE)
    if soq_match:
        return standardize_date(soq_match.group(1))
    
    # Look for "Deadline: MM/DD/YYYY"
    deadline_match = re.search(r"Deadline[:\s]*(\d{1,2}/\d{1,2}/\d{4})", content_text, re.IGNORECASE)
    if deadline_match:
        return standardize_date(deadline_match.group(1))
    
    # Look for "Due: MM/DD/YYYY"
    due_match = re.search(r"Due[:\s]*(\d{1,2}/\d{1,2}/\d{4})", content_text, re.IGNORECASE)
    if due_match:
        return standardize_date(due_match.group(1))
    
    return None

def extract_boston_comments(soup, content_text):
    """
    Extract project description and location for comments
    """
    comments_parts = []
    
    # Look for location information
    location_match = re.search(r"Location[:\s]*([^\n]+)", content_text, re.IGNORECASE)
    if location_match:
        comments_parts.append(f"Location: {location_match.group(1).strip()}")
    
    # Look for project description/narrative paragraphs
    paragraphs = soup.find_all("p")
    for p in paragraphs:
        text = p.get_text(strip=True)
        if len(text) > 100 and any(word in text.lower() for word in ["project", "services", "scope", "background"]):
            comments_parts.append(text)
            break  # Take first substantial description
    
    return " | ".join(comments_parts) if comments_parts else None

def extract_boston_instructions(content_text):
    """
    Extract submission instructions and requirements
    """
    instructions_parts = []
    
    # Look for submission requirements
    submission_patterns = [
        r"Submission[:\s]*([^\n.]+)",
        r"USB flash drives[^\n.]+",
        r"Sealed package[^\n.]+",
        r"PDF format[^\n.]+"
    ]
    
    for pattern in submission_patterns:
        matches = re.findall(pattern, content_text, re.IGNORECASE)
        for match in matches:
            if len(match.strip()) > 10:
                instructions_parts.append(match.strip())
    
    return " | ".join(instructions_parts[:3]) if instructions_parts else None

def extract_boston_standard_forms(content_text):
    """
    Extract Boston-specific standard forms and requirements
    """
    standard_forms = []
    
    # Boston-specific requirements
    boston_requirements = [
        "Prevailing Wages Apply",
        "DCAMM Certification",
        "MWBE",
        "CORI",
        "EPP"
    ]
    
    for requirement in boston_requirements:
        if requirement.lower() in content_text.lower():
            standard_forms.append(requirement)
    
    # Add UNSPSC code if present
    unspsc_match = re.search(r"UNSPSC[:\s]*(\d+)", content_text, re.IGNORECASE)
    if unspsc_match:
        standard_forms.append(f"UNSPSC: {unspsc_match.group(1)}")
    
    return ", ".join(standard_forms) if standard_forms else None

def extract_boston_bid_forms(soup):
    """
    Extract bid-specific forms and documents from links
    """
    bid_forms = []
    links = soup.find_all("a", href=True)
    
    for link in links:
        href = link["href"]
        link_text = link.get_text(strip=True)
        
        # Look for document links
        if any(ext in href.lower() for ext in [".pdf", ".doc", ".xls", ".docx"]):
            if any(word in link_text.lower() for word in ["form", "spec", "drawing", "addendum", "attachment", "document"]):
                bid_forms.append(link_text)
    
    return ", ".join(bid_forms[:5]) if bid_forms else None

def standardize_date(date_str):
    """
    Standardize Boston's date formats
    """
    if not date_str or date_str.strip() == "":
        return None
    
    date_str = date_str.strip()
    
    try:
        # Try common formats
        for fmt in ["%B %d, %Y at %I:%M%p", "%B %d, %Y", "%m/%d/%Y", "%Y-%m-%d"]:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # If all parsing fails, return original
        print(f"⚠️ Could not parse Boston date: '{date_str}'")
        return date_str
        
    except Exception:
        return date_str

def determine_status(due_date_str):
    """
    Determine if bid is open, upcoming, or closed based on due date
    """
    if not due_date_str:
        return "Open"
    
    try:
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
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
        print("\nBoston bid data:")
        print(df[['Title', 'Due Date', 'Department', 'Industry']].head())
    else:
        print("No data retrieved")