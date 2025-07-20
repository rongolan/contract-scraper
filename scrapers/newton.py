from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

# ----------------------------
# Selenium Scraper for Town of Newton, MA
# ----------------------------

def scrape():
    url = "https://www.newtonma.gov/government/purchasing/current-bids"

    # Browser setup for both local and Heroku environments
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")  # Heroku compatibility
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
    
    # Set Chrome binary path for Heroku (buildpack sets this environment variable)
    import os
    chrome_bin = os.environ.get('GOOGLE_CHROME_BIN')
    if chrome_bin:
        options.binary_location = chrome_bin

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        # Allow time for page to render
        time.sleep(5)

        # DEBUG: Verify presence of 'listtable' in rendered HTML
        page_src = driver.page_source
        print("🔍 'listtable' in page source?", "listtable" in page_src)
        start = page_src.find("listtable")
        if start != -1:
            snippet = page_src[start-100:start+500]
            print("🔍 snippet around 'listtable':\n", snippet)
        else:
            print("🔍 'listtable' not found in page source.")

        soup = BeautifulSoup(page_src, "html.parser")
        table = soup.find("table", class_="listtable")
        if not table:
            print("❌ Could not find listtable on Newton page.")
            return pd.DataFrame()

        # Parse rows
        rows = []
        tbody = table.find("tbody")
        tr_elements = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]
        for tr in tr_elements:
            title_cell   = tr.find("td", {"data-th": "Title"})
            start_cell   = tr.find("td", {"data-th": "Starting"})
            closing_cell = tr.find("td", {"data-th": "Closing"})
            status_cell  = tr.find("td", {"data-th": "Status"})

            if not title_cell or not start_cell or not closing_cell or not status_cell:
                continue

            raw_status = status_cell.get_text(strip=True).strip()
            # Include Open and Pending (map Pending -> Upcoming)
            if raw_status.lower() == "open":
                status = "open"
            elif raw_status.lower() == "pending":
                status = "upcoming"
            else:
                continue  # skip closed or other statuses

            # Title & URL
            link = title_cell.find("a")
            title = link.get_text(strip=True) if link else title_cell.get_text(strip=True)
            href  = link["href"] if link and link.has_attr("href") else ""
            source_url = f"https://www.newtonma.gov{href}" if href.startswith("/") else href

            # Dates
            release_date = start_cell.get_text(strip=True)
            due_date     = closing_cell.get_text(strip=True)

            rows.append({
                "Title": title,
                "Department": None,
                "Industry": None,
                "Estimated Value": None,
                "Release Date": release_date,
                "Due Date": due_date,
                "Instructions": None,
                "Bid Deposit": None,
                "Addendum": None,
                "City": "Newton",
                "Source Type": "Open Bids",
                "Source URL": source_url,
                "status": status
            })

        df = pd.DataFrame(rows, columns=[
            "Title", "Department", "Industry", "Estimated Value",
            "Release Date", "Due Date", "Instructions", "Bid Deposit",
            "Addendum", "City", "Source Type", "Source URL", "status"
        ])
        print("✅ Newton data scraped with Selenium:")
        print(df.head())
        return df

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()