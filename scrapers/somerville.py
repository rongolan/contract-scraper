import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

def scrape():
    url = "https://www.somervillema.gov/departments/finance/procurement-and-contracting-services"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # ----------------------------
    # Scrape the on-page table
    # ----------------------------
    table = soup.find("table")
    rows = []
    if table:
        headers = [th.get_text(strip=True).replace("Sort ascending", "").strip() for th in table.find_all("th")]
        for tr in table.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells:
                rows.append(cells)
    df_web = pd.DataFrame(rows, columns=headers)
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
        "Bid Notice": "Source URL"
    })

    df_web_renamed["Department"] = None
    df_web_renamed["Industry"] = None
    df_web_renamed["City"] = "Somerville"
    df_web_renamed["Estimated Value"] = None
    df_web_renamed["Source Type"] = "Open Bids"

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
        df_excel_renamed["Release Date"] = df_excel_renamed["Month"].astype(str) + "/01/" + df_excel_renamed["Year"].astype(str)
        df_excel_renamed["Due Date"] = None
        df_excel_renamed["Instructions"] = None
        df_excel_renamed["Bid Deposit"] = None
        df_excel_renamed["Addendum"] = None
        df_excel_renamed["City"] = "Somerville"
        df_excel_renamed["Source Type"] = "Upcoming Bids"
        df_excel_renamed["Source URL"] = url
    else:
        df_excel_renamed = pd.DataFrame(columns=df_web_renamed.columns)

    # ----------------------------
    # Final formatting
    # ----------------------------
    columns = [
        "Title", "Department", "Industry", "Estimated Value",
        "Release Date", "Due Date", "Instructions", "Bid Deposit",
        "Addendum", "City", "Source Type", "Source URL"
    ]
    df_web_clean = df_web_renamed[columns]
    df_excel_clean = df_excel_renamed[columns]

    df_combined = pd.concat([df_web_clean, df_excel_clean], ignore_index=True)

    # Add status
    def determine_status(due_date_str):
        if pd.isna(due_date_str) or due_date_str.strip() == "":
            return "Upcoming"
        try:
            due = datetime.strptime(due_date_str, "%m/%d/%Y - %I:%M%p")
            return "Open" if due > datetime.now() else "Closed"
        except ValueError:
            return "Open"

    df_combined["status"] = df_combined["Due Date"].apply(determine_status)

    return df_combined
