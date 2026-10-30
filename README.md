# WebScrappingL

A Python-based web scraping component developed for the **Sinhala Newspaper Summarization System** research project.

## Project Overview

This branch focuses exclusively on collecting Sinhala news articles from three Sri Lankan newspaper websites:

- [Lankadeepa](https://www.lankadeepa.lk/)
- [Ada Derana](https://www.adaderana.lk/)
- [Hiru News](https://www.hirunews.lk/)

The purpose of this component is to retrieve individual news articles and store their information in a centralized SQLite database.

The collected data serves as the input for subsequent research and development stages.&#x20;

## Features

- Collects news articles from three Sri Lankan newspaper websites.
- Extracts individual article headlines and full article text.
- Retrieves article URLs and available publication times.
- Stores newspaper source information and collected articles in SQLite.
- Prevents duplicate article insertion using article URLs.
- Updates missing information when existing articles are collected again.
- Preserves separate articles from different newspapers, even when they report the same news story.
- Runs all newspaper collectors through a centralized execution workflow.
- Repeats the collection process at configurable intervals.
- Handles individual website collection failures without stopping other collectors.

## Project Structure

```text
WebScrappingL/
│
├── Lankadeepa.py          # Lankadeepa news collector
├── adaDerana.py           # Ada Derana news collector
├── Hirunews.py            # Hiru News collector
│
├── database.py            # Shared SQLite database operations
├── create_database.py     # Database initialization and verification
├── main.py                # Main collection workflow
│
├── newspaper_news.db      # SQLite database
├── requirements.txt       # Project dependencies
└── README.md
```

## Technologies Used

- **Python** – Main programming language
- **Requests** – HTTP requests to newspaper websites
- **BeautifulSoup4** – HTML parsing and content extraction
- **lxml** – HTML parsing backend
- **SQLite** – Database storage

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd WebScrappingL
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize the database

```bash
python create_database.py
```

### 6. Run the collection system

```bash
python main.py
```

The main script executes all three newspaper collectors and repeats the collection process every 60 seconds.

## Database

Collected information is stored in `newspaper_news.db`.

The database maintains:

- Newspaper source information
- Individual article headlines
- Full article text
- Article URLs
- Available publication timestamps
- Collection timestamps
- Story associations, where applicable

Each distinct article is retained as a separate record. Duplicate URL detection prevents the same article from being inserted repeatedly.

## Development Scope

This branch covers only the web scraping and data collection stage of the overall research project.

**Completed:**

- [x] Lankadeepa news collector
- [x] Ada Derana news collector
- [x] Hiru News collector
- [x] Shared SQLite database
- [x] Centralized database operations
- [x] Duplicate URL detection
- [x] Main collection workflow
- [x] Periodic news collection

**Future work outside this branch:**

- Sinhala news similarity detection and story grouping
- Multi-source news summarization
- User-configurable summary durations
- Text-to-speech functionality
- Desktop or mobile application development

## Responsible Web Scraping

- Respect website terms of service and applicable access restrictions.
- Check `robots.txt` where applicable.
- Use reasonable request intervals.
- Avoid unnecessary requests to newspaper websites.
- Retain source URLs and collection timestamps for research traceability.

##
