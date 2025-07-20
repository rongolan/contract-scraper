from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape():
    base_url = "https://procurement.opengov.com"
    portal_url = f"{base_url}/portal/cambridgema"

    options = Options()
    #options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.get(portal_url)

    try:
        # Wait for project cards to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='project-card-link']"))
        )
        time.sleep(2)  # Ensure any final JS rendering is done
        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.select("[data-testid='project-card-link']")
        print(f"🔍 Found {len(cards)} project cards")

        rows = []
        for card in cards:
            title = card.get_text(strip=True)
            relative_url = card.get("href")
            full_url = f"{base_url}{relative_url}" if relative_url else None

            rows.append({
                "Title": title,
                "Department": None,
                "Industry": None,
                "Estimated Value": None,
                "Release Date": None,
                "Due Date": None,
                "Instructions": None,
                "Bid Deposit": None,
                "Addendum": None,
                "City": "Cambridge",
                "Source Type": "Open Bids",
                "Source URL": full_url,
                "Status": "Open"
            })

        df = pd.DataFrame(rows)
        print("✅ Cambridge data scraped with Selenium:")
        print(df.head())
        return df

    except Exception as e:
        print(f"❌ Error during Selenium scraping: {e}")
        return pd.DataFrame()

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()
