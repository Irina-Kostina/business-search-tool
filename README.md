# NZ Business Outreach Agent

### A Python automation tool that finds New Zealand small businesses, extracts their contact details, and saves the data into Google Sheets for easy outreach.

---

## Overview

**NZ Business Outreach Agent** is a lightweight Python automation tool that helps freelancers and small teams discover local New Zealand businesses and collect their public contact details automatically.

Simply enter a search query (e.g., `nail salon Auckland`, `dog groomer Wellington`, `wedding photographer NZ`) and the agent will:

- Search DuckDuckGo for relevant local business websites
- Filter out non-business and irrelevant results
- Open each website and extract:
  - business name
  - website URL
  - email addresses
  - phone numbers
  - Instagram links
  - Facebook links
- Avoid duplicates
- Save everything into a connected **Google Sheet**

This tool eliminates manual research and makes outreach 10× faster.

---

## Features

### Smart Search

Uses DuckDuckGo’s HTML results to find real NZ businesses.  
Includes NZ-focused search filtering (`site:co.nz`, `site:.nz`).

### Website Parsing

Automatically extracts:

- Emails
- Phone numbers
- Social profiles
- Business name
- Metadata

### Duplicate Protection

Already saved a business once?  
The agent skips it automatically.

### Google Sheets Integration

Outputs clean structured data directly to a Google Sheet using a secure service account.

### No fragile APIs

No Google Search API, no paid keys, no unreliable third-party libraries.  
Everything runs locally and reliably.

---

## Use Cases

- Freelance outreach (web developers, designers, SMM)
- Lead generation
- Market research
- Local business discovery
- Building your own AI-powered outreach agent
- Automating cold email list creation

---

## How It Works (High-Level)

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

### Usage

Run:

```bash
python main.py
```

Enter a search query:
nail salon Auckland
Enter number of results:
5

Check your Google Sheet — the leads will appear there automatically.

### Why This Tool Exists

Manually researching small businesses for outreach is slow and painful.
This tool was created to:

automate the boring parts

save hours of manual searching

give freelancers an edge

provide clean, structured leads instantly

It’s especially useful for those targeting NZ small businesses, where online presence is inconsistent and manually searching is time-consuming.

### Author

Developed by Irina Kostina
A web developer and automation enthusiast based in New Zealand.
