# NZ Business Outreach Agent

### A Python utility that helps users discover publicly available information about New Zealand businesses and store collected data in Google Sheets for easier review and analysis.

---

## Overview

**NZ Business Research Agent** is a small script that lets you explore local NZ businesses by collecting basic information from websites found through web searches.

When you enter a search term (for example: “dog groomer Wellington”, “wedding photographer NZ”), the tool will:

- Search DuckDuckGo for websites related to your query
- Skip common non-business sites (like social media links)
- Open each website and gather publicly available information:
- Business name (from the page title)
- Website URL
- Email addresses shown on the page
- Avoid adding the same website twice
- Save everything into a Google Sheet that you connect to

This tool is meant to help organise and review publicly available business information. Any use of the collected data should follow all relevant laws, website terms, and ethical guidelines.

---

## Features

### Smart Search

Uses DuckDuckGo’s HTML results to find real NZ businesses.  
Includes NZ-focused search filtering (`site:co.nz`, `site:.nz`).

### Website Parsing

Automatically extracts:

- Emails
- Phone numbers
- Business name

### Duplicate Protection

Already saved a business once?  
The agent skips it automatically.

### Google Sheets Integration

Outputs clean structured data directly to a Google Sheet using a secure service account.

### No fragile APIs

No Google Search API, no paid keys, no unreliable third-party libraries.  
Everything runs locally and reliably.

---

## How It Works

1. **User enters a search term**

2. **Agent fetches DuckDuckGo results page**  
   (simple HTML request → reliable and fast)

3. **Extracts website links**  
   Filters out Facebook, Instagram, Wikipedia, news sites, etc.

4. **Opens each business website**  
   Parses text using BeautifulSoup.

5. **Extracts useful contact information.**

6. **Saves everything to Google Sheets**  
   Avoids duplicates automatically.

---

## Technologies Used

- **Python 3.10+**
- **Requests** (HTML fetching)
- **BeautifulSoup** (HTML parsing)
- **Google Sheets API**
- **Service Account Authentication**
- **dotenv** for managing environment variables
<!-- - **Streamlit** _(optional, for UI interface)_ -->

---

## Installation

Clone the repo:

```bash
git clone https://github.com/yourusername/nz-business-outreach-agent.git
cd nz-business-outreach-agent
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Add .env:

```bash
SPREADSHEET_ID=your_google_sheet_id
```

Add your Google Cloud service account JSON file:

```bash
google-credentials.json
```

---

### Usage

Run:

```bash
python main.py
```

Enter a search query:
dog grooming Auckland
Enter number of results:
5

Check your Google Sheet — the list will appear there automatically.

---

### Author

Developed by Irina Kostina
A web developer and automation enthusiast based in New Zealand.
