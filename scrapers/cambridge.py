import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape():
    base_url = "https://procurement.opengov.com"
    portal_url = f"{base_url}/portal/cambridgema"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "Accept": "text/html",
        "Referer": portal_url
    }

    response = requests.get(portal_url, headers=headers)
    if not response.ok:
        print(f"❌ Error fetching page. Status: {response.status_code}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.find_all("a", {"data-testid": "project-card-link"})

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
    print("✅ Cambridge data scraped from HTML:")
    print(df.head())
    return df

# If running directly, test the scrape
if __name__ == "__main__":
    scrape()
