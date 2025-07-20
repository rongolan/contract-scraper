import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

def scrape():
    url = "https://concordma.gov/bids.aspx"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    print(soup.prettify()[:2000])  # Print the first 2000 characters

    container = soup.find("div", class_="listItems")
    if not container:
        raise ValueError("Could not find the bid listings container.")

    rows = []
    bid_rows = container.find_all("div", class_="listItemsRow")
    for row in bid_rows:
        title_div = row.find("div", class_="bidTitle")
        status_div = row.find("div", class_="bidStatus")

        # Title and detail URL
        title_link = title_div.find("a") if title_div else None
        title = title_link.get_text(strip=True) if title_link else "No title found"
        relative_url = title_link["href"] if title_link and title_link.has_attr("href") else ""
        detail_url = f"https://concordma.gov/{relative_url}" if relative_url else ""

        # Status and closing date
        spans = status_div.find_all("span") if status_div else []
        status = spans[2].get_text(strip=True) if len(spans) > 2 else "Unknown"
        closing_date = spans[3].get_text(strip=True) if len(spans) > 3 else "Unknown"

        # Fetch detail page to get additional info
        release_date = None
        # Initialize estimated value
        estimated_value = None
        
        if detail_url:
            try:
                detail_response = requests.get(detail_url)
                detail_soup = BeautifulSoup(detail_response.text, "html.parser")
                all_trs = detail_soup.find_all("tr")
                
                # Look for both Publication Date and Estimated Value
                for idx, tr in enumerate(all_trs):
                    label_span = tr.find("span", class_="BidListHeader")
                    if label_span:
                        label_text = label_span.get_text(strip=True)
                        
                        # Look for Publication Date/Time
                        if "Publication Date/Time" in label_text:
                            if idx + 1 < len(all_trs):
                                next_tr = all_trs[idx + 1]
                                value_span = next_tr.find("span", class_="BidDetail")
                                if value_span:
                                    release_date = value_span.get_text(strip=True)
                        
                        # Look for contract value indicators
                        elif any(keyword in label_text.lower() for keyword in [
                            "estimated", "budget", "value", "cost", "amount", "price"
                        ]):
                            if idx + 1 < len(all_trs):
                                next_tr = all_trs[idx + 1]
                                value_span = next_tr.find("span", class_="BidDetail")
                                if value_span:
                                    value_text = value_span.get_text(strip=True)
                                    # Extract numeric value from text like "$1,500,000" or "1500000"
                                    value_match = re.search(r'[\d,]+(?:\.\d{2})?', value_text.replace('$', '').replace(',', ''))
                                    if value_match:
                                        try:
                                            estimated_value = int(float(value_match.group()))
                                            print(f"   💵 Found estimated value: ${estimated_value:,} for {title}")
                                        except ValueError:
                                            pass
                
                # Also check the general page text for value patterns if not found in structured data
                if not estimated_value:
                    page_text = detail_soup.get_text().lower()
                    value_patterns = [
                        r'estimated\s+(?:cost|value|amount)[:]?\s*\$?([\d,]+(?:\.\d{2})?)',
                        r'budget[:]?\s*\$?([\d,]+(?:\.\d{2})?)',
                        r'not\s+to\s+exceed\s*\$?([\d,]+(?:\.\d{2})?)',
                        r'\$\s*([\d,]+(?:\.\d{2})?)'
                    ]
                    
                    for pattern in value_patterns:
                        match = re.search(pattern, page_text)
                        if match:
                            try:
                                clean_value = match.group(1).replace(',', '')
                                estimated_value = int(float(clean_value))
                                print(f"   💵 Found estimated value in text: ${estimated_value:,} for {title}")
                                break
                            except ValueError:
                                continue
                                
            except Exception as e:
                print(f"Failed to fetch details for {detail_url}: {e}")

        row_data = {
            "Title": title,
            "Department": None,
            "Industry": None,
            "Estimated Value": estimated_value,
            "Release Date": release_date,
            "Due Date": closing_date,
            "Instructions": None,
            "Bid Deposit": None,
            "Addendum": None,
            "City": "Concord",
            "Source Type": "Open Bids",
            "Source URL": detail_url,
            "status": status
        }
        rows.append(row_data)

    df = pd.DataFrame(rows, columns=[
        "Title", "Department", "Industry", "Estimated Value", "Release Date",
        "Due Date", "Instructions", "Bid Deposit", "Addendum",
        "City", "Source Type", "Source URL", "status"
    ])
    return df

if __name__ == "__main__":
    df = scrape()
    print(df)