import os
import re
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

import gspread
from google.oauth2.service_account import Credentials


# =====================
# 1. Load environment variables
# =====================

load_dotenv()
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")


# =====================
# Parsing helpers
# =====================

def clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split())


def extract_emails(text: str):
    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    return list(set(re.findall(pattern, text)))


def get_page_html(url: str) -> str:
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            )
        }
        r = requests.get(url, headers=headers, timeout=10)
        return r.text if r.status_code == 200 else ""
    except:
        return ""


def parse_business_info(url: str, query: str):
    html = get_page_html(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Business name guess from <title>
    title_tag = soup.find("title")
    business_name = clean_text(title_tag.get_text()) if title_tag else urlparse(url).netloc

    text = soup.get_text(" ", strip=True)[:8000]
    emails = extract_emails(text)

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "search_query": query,
        "business_name": business_name,
        "website": url,
        "emails": ", ".join(emails),
    }


# =====================
# DuckDuckGo HTML search
# =====================

def _decode_ddg_redirect(url: str):
    parsed = urlparse(url)
    if parsed.netloc == "duckduckgo.com" and parsed.path.startswith("/l/"):
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return url


def search_business_urls(query: str, num_results: int):
    print(f"[+] Searching DuckDuckGo for: {query}")

    ddg_query = f"{query} site:co.nz OR site:.nz"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": ddg_query},
            headers=headers,
            timeout=10,
        )
    except:
        print("[!] Error connecting to DuckDuckGo")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    urls = []

    for a in soup.select("a.result__a"):
        href = a.get("href")
        if not href:
            continue
        real = _decode_ddg_redirect(href)
        urls.append(real)
        if len(urls) >= num_results * 3:
            break

    skip = ["facebook", "linkedin", "instagram", "youtube", "mayo", "clinic", "healthline"]
    cleaned = [u for u in urls if not any(s in u.lower() for s in skip)]

    cleaned = list(dict.fromkeys(cleaned))  # dedupe
    cleaned = cleaned[:num_results]

    print(f"[+] Found {len(cleaned)} usable URLs")
    return cleaned


# =====================
# Google Sheets
# =====================

def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    creds = Credentials.from_service_account_file(
        "google-credentials.json", scopes=scopes
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).sheet1


def ensure_headers(sheet):
    existing = sheet.get_all_values()
    if existing:
        return

    sheet.append_row(
        [
            "timestamp",
            "search_query",
            "business_name",
            "website",
            "emails",
        ],
        value_input_option="RAW",
    )


def get_existing_websites(sheet):
    try:
        col = sheet.col_values(4)  # Column D = website
    except:
        return set()

    if len(col) <= 1:
        return set()

    return set(col[1:])  # skip header


def append_lead(sheet, info):
    sheet.append_row(
        [
            info["timestamp"],
            info["search_query"],
            info["business_name"],
            info["website"],
            info["emails"],
        ],
        value_input_option="RAW",
    )


# =====================
# Main script
# =====================

def main():
    print("=== NZ Business Outreach Agent ===")

    query = input("Enter search query: ").strip()
    if not query:
        return

    try:
        num = int(input("How many websites to process: ").strip())
    except:
        num = 5

    urls = search_business_urls(query, num)
    if not urls:
        print("No results found.")
        return

    sheet = get_sheet()
    ensure_headers(sheet)
    existing = get_existing_websites(sheet)

    print("\n[+] Processing...\n")

    for i, url in enumerate(urls, start=1):
        print(f"[{i}/{len(urls)}] {url}")

        if url in existing:
            print("   Duplicate → skipped.\n")
            continue

        info = parse_business_info(url, query)
        if not info:
            print("   Could not parse → skipped.\n")
            continue

        print(f"   Business name: {info['business_name']}")
        print(f"   Emails: {info['emails'] or 'None'}")

        append_lead(sheet, info)
        existing.add(url)

        print("   → Saved.\n")
        time.sleep(1.5)

    print("[+] Done!")


if __name__ == "__main__":
    main()
