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

load_dotenv()  # loads SPREADSHEET_ID from .env

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")


# =====================
# 2. Helper functions (parsing website content)
# =====================

def clean_text(text: str) -> str:
    """Normalise whitespace in a string."""
    if not text:
        return ""
    return " ".join(text.split())


def extract_emails(text: str):
    """Find email addresses using regex."""
    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    emails = re.findall(pattern, text)
    return list(set(emails))


def extract_phones(text: str):
    """Simple phone regex (not perfect, but OK for first version)."""
    pattern = r"(\+?\d[\d\s().-]{7,}\d)"
    phones = re.findall(pattern, text)
    cleaned = [p.strip() for p in phones]
    return list(set(cleaned))


def extract_social_links(text: str):
    """Find Instagram and Facebook links."""
    insta_pattern = r"(https?://(?:www\.)?instagram\.com/[^\s\"']+)"
    fb_pattern = r"(https?://(?:www\.)?facebook\.com/[^\s\"']+)"

    insta_matches = re.findall(insta_pattern, text)
    fb_matches = re.findall(fb_pattern, text)

    insta = insta_matches[0] if insta_matches else ""
    fb = fb_matches[0] if fb_matches else ""

    return insta, fb


def get_page_html(url: str) -> str:
    """Download HTML for a URL with browser-like headers."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"    [!] Failed to fetch ({resp.status_code})")
            return ""
    except Exception as e:
        print(f"    [!] Error fetching {url}: {e}")
        return ""


def parse_business_info(url: str, query: str) -> dict | None:
    """
    Open website and extract:
    - business name (from <title> or domain)
    - emails
    - phones
    - instagram + facebook
    """
    html = get_page_html(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # <title> as a simple business name guess
    title_tag = soup.find("title")
    title = clean_text(title_tag.get_text()) if title_tag else ""

    # meta description (for context)
    desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_desc = clean_text(desc_tag["content"]) if desc_tag and desc_tag.get("content") else ""

    # Text for regex scanning
    body_text = soup.get_text(separator=" ", strip=True)
    body_short = body_text[:8000]  # limit length

    emails = extract_emails(body_short)
    phones = extract_phones(body_short)
    insta, fb = extract_social_links(body_short)

    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    business_name = title or domain or url

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "search_query": query,
        "business_name": business_name,
        "website": url,
        "title": title,
        "description": meta_desc,
        "emails": ", ".join(emails),
        "phones": ", ".join(phones),
        "instagram": insta,
        "facebook": fb,
    }


# =====================
# 2b. Search functions (DuckDuckGo via HTML)
# =====================

def _decode_ddg_redirect(url: str) -> str:
    """
    DuckDuckGo HTML results use links like:
    /l/?kh=-1&uddg=<encoded real url>
    This function extracts the real URL if possible.
    """
    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return url


def search_business_urls(query: str, num_results: int = 10):
    """
    Search DuckDuckGo by downloading the HTML results page.
    We avoid external libraries because they behave inconsistently.
    """
    print(f"[+] Searching DuckDuckGo (HTML) for: {query}")

    # Focus on NZ commercial sites
    ddg_query = f"{query} site:co.nz OR site:.nz"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": ddg_query},
            headers=headers,
            timeout=10,
        )
    except Exception as e:
        print(f"[!] Error calling DuckDuckGo: {e}")
        return []

    if resp.status_code != 200:
        print(f"[!] DuckDuckGo returned status {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    urls: list[str] = []
    # 'a.result__a' are the result links in the HTML interface
    for a in soup.select("a.result__a"):
        href = a.get("href")
        if not href:
            continue
        real_url = _decode_ddg_redirect(href)
        urls.append(real_url)
        if len(urls) >= num_results * 3:
            break

    print(f"[+] Got {len(urls)} raw URLs from search.")

    # Filter out obvious non-business / social / big info sites
    skip_domains = [
        "facebook.com", "instagram.com", "linkedin.com", "x.com",
        "youtube.com", "wikipedia.org",
        "mayo", "clinic", "healthline", ".govt.nz"
    ]

    filtered = []
    for u in urls:
        lower = u.lower()
        if any(bad in lower for bad in skip_domains):
            continue
        filtered.append(u)

    # Remove duplicates while keeping order
    filtered = list(dict.fromkeys(filtered))
    filtered = filtered[:num_results]

    print(f"[+] Got {len(filtered)} filtered URLs.")
    return filtered


# =====================
# 3. Google Sheets setup
# =====================

def get_sheet():
    """
    Authorise with service account and get the first worksheet of the spreadsheet.
    """
    if not SPREADSHEET_ID:
        raise RuntimeError("SPREADSHEET_ID is not set. Add it to .env.")

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    creds = Credentials.from_service_account_file(
        "google-credentials.json",
        scopes=scopes,
    )

    client_gsheet = gspread.authorize(creds)

    sheet = client_gsheet.open_by_key(SPREADSHEET_ID).sheet1
    return sheet


def ensure_headers(sheet):
    """
    If the sheet is empty, write the header row.
    """
    existing = sheet.get_all_values()
    if existing:
        return  # already has data

    headers = [
        "timestamp",
        "search_query",
        "business_name",
        "website",
        "title",
        "description",
        "emails",
        "phones",
        "instagram",
        "facebook",
    ]
    sheet.append_row(headers, value_input_option="RAW")


def append_lead(sheet, info: dict):
    """
    Append one row (one business) to the sheet.
    """
    row = [
        info.get("timestamp", ""),
        info.get("search_query", ""),
        info.get("business_name", ""),
        info.get("website", ""),
        info.get("title", ""),
        info.get("description", ""),
        info.get("emails", ""),
        info.get("phones", ""),
        info.get("instagram", ""),
        info.get("facebook", ""),
    ]

    sheet.append_row(row, value_input_option="RAW")


def get_existing_websites(sheet):
    """
    Read existing websites from column D (4th column) to avoid duplicates.
    Assumes the first row is headers.
    """
    try:
        values = sheet.col_values(4)  # column 4 = 'website'
    except Exception:
        return set()

    if not values:
        return set()

    # skip header row
    return set(values[1:])


# =====================
# 4. Main script
# =====================

def main():
    print("=== AI Outreach Agent for NZ Businesses (v0 - no AI emails yet) ===\n")

    query = input("Enter search query (e.g. 'nail salon Auckland'): ").strip()
    if not query:
        print("No query given. Exiting.")
        return

    try:
        num_results = int(input("How many websites to process (e.g. 5 or 10): ").strip())
    except ValueError:
        num_results = 5

    urls = search_business_urls(query, num_results=num_results)

    if not urls:
        print("No URLs found. Exiting.")
        return

    try:
        sheet = get_sheet()
    except Exception as e:
        print(f"[!] Error connecting to Google Sheet: {e}")
        return

    ensure_headers(sheet)
    existing_websites = get_existing_websites(sheet)

    print("\n[+] Starting to process websites...\n")

    for i, url in enumerate(urls, start=1):
        print(f"[{i}/{len(urls)}] {url}")

        info = parse_business_info(url, query)
        if not info:
            print("    Skipped (could not parse).")
            continue

        print(f"    Business name guess: {info['business_name']}")
        print(f"    Emails: {info['emails'] or 'None'}")
        print(f"    Phones: {info['phones'] or 'None'}")
        print(f"    Instagram: {info['instagram'] or 'None'}")
        print(f"    Facebook: {info['facebook'] or 'None'}")

        # Avoid duplicates by website URL
        if info["website"] in existing_websites:
            print("    Already in sheet → skipping (duplicate).\n")
            continue

        append_lead(sheet, info)
        existing_websites.add(info["website"])
        print("    → Saved to Google Sheet.\n")

        # Small pause to be polite to servers
        time.sleep(2)

    print("\n[+] Done! Check your Google Sheet for new leads.")


if __name__ == "__main__":
    main()
