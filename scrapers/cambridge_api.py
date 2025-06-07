import requests
import pandas as pd

# ----------------------------
# Scraper for City of Cambridge via OpenGov
# ----------------------------

def scrape():
    api_url = "https://procurement.opengov.com/api/procurements?portal_slug=cambridgema&sort_by=closing_date&status=open"
    
    headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://procurement.opengov.com/portal/cambridgema"
}
    response = requests.get(api_url, headers=headers)

    if not response.ok or not response.text.strip():
        print(f"❌ Error fetching data from OpenGov. Status: {response.status_code}, Body: {response.text[:200]}")
        return pd.DataFrame()

    try:
        data = response.json()
    except ValueError as e:
        print(f"❌ Failed to parse JSON: {e}")
        return pd.DataFrame()

    rows = []
    for item in data.get("data", []):
        attributes = item.get("attributes", {})

        rows.append({
            "Title": attributes.get("title"),
            "Department": attributes.get("department"),
            "Industry": None,
            "Estimated Value": None,
            "Release Date": None,
            "Due Date": attributes.get("closing_date"),
            "Instructions": None,
            "Bid Deposit": None,
            "Addendum": None,
            "City": "Cambridge",
            "Source Type": "Open Bids",
            "Source URL": f"https://procurement.opengov.com{attributes.get('public_url', '')}",
            "Status": attributes.get("status", "Open").capitalize()
        })

    df = pd.DataFrame(rows)
    print("✅ Cambridge data scraped:")
    print(df.head())
    return df

# If running this module directly, test the output
if __name__ == "__main__":
    scrape()
