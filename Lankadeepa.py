
import requests
import re
import sqlite3
import sys
import time

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone, timedelta


# Keep Sinhala text readable in Windows terminals and redirected output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ==================================================
# 1. SETTINGS
# ==================================================

HOME_URL = "https://www.lankadeepa.lk/"
CHECK_INTERVAL = 60

# Sri Lanka time: UTC+5:30
SL_TIMEZONE = timezone(timedelta(hours=5, minutes=30))

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)


# ==================================================
# 2. DATABASE SETUP
# ==================================================

connection = sqlite3.connect("newspaper_news.db")
connection.execute("PRAGMA foreign_keys = ON")

connection.execute("""
CREATE TABLE IF NOT EXISTS newspapers (
    newspaper_id INTEGER PRIMARY KEY AUTOINCREMENT,
    newspaper_name TEXT NOT NULL UNIQUE,
    website_url TEXT NOT NULL UNIQUE,
    language TEXT NOT NULL
)
""")

connection.execute("""
CREATE TABLE IF NOT EXISTS stories (
    story_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_title TEXT NOT NULL,
    category TEXT,
    first_seen_time TEXT NOT NULL
)
""")

connection.execute("""
CREATE TABLE IF NOT EXISTS articles (
    article_id INTEGER PRIMARY KEY AUTOINCREMENT,
    newspaper_id INTEGER NOT NULL,
    headline TEXT NOT NULL,
    article_text TEXT,
    article_url TEXT NOT NULL UNIQUE,
    published_time TEXT,
    collected_time TEXT NOT NULL,
    story_id INTEGER,
    generated_summary TEXT,
    FOREIGN KEY (newspaper_id) REFERENCES newspapers(newspaper_id),
    FOREIGN KEY (story_id) REFERENCES stories(story_id)
)
""")

# Remove the temporary story_groups table used by an earlier schema.
legacy_story_groups = connection.execute("""
SELECT name
FROM sqlite_master
WHERE type = 'table' AND name = 'story_groups'
""").fetchone()
if legacy_story_groups:
    connection.execute("""
    INSERT OR IGNORE INTO stories (
        story_id, story_title, first_seen_time
    )
    SELECT story_group_id, group_title, created_time
    FROM story_groups
    """)
    connection.execute("DROP TABLE story_groups")

# Migrate the original denormalized articles table without losing records.
article_columns = {
    row[1] for row in connection.execute("PRAGMA table_info(articles)")
}
if "newspaper_id" not in article_columns:
    connection.execute("""
    INSERT OR IGNORE INTO newspapers (
        newspaper_name, website_url, language
    )
    VALUES (?, ?, ?)
    """, ("Lankadeepa", HOME_URL, "Sinhala"))

    connection.execute("""
    ALTER TABLE articles RENAME TO articles_legacy
    """)
    connection.execute("""
    CREATE TABLE articles (
        article_id INTEGER PRIMARY KEY AUTOINCREMENT,
        newspaper_id INTEGER NOT NULL,
        headline TEXT NOT NULL,
        article_text TEXT,
        article_url TEXT NOT NULL UNIQUE,
        published_time TEXT,
        collected_time TEXT NOT NULL,
        story_id INTEGER,
        generated_summary TEXT,
        FOREIGN KEY (newspaper_id) REFERENCES newspapers(newspaper_id),
        FOREIGN KEY (story_id) REFERENCES stories(story_id)
    )
    """)
    connection.execute("""
    INSERT INTO articles (
        article_id,
        newspaper_id,
        headline,
        article_text,
        article_url,
        published_time,
        collected_time,
        story_id,
        generated_summary
    )
    SELECT
        legacy.article_id,
        newspaper.newspaper_id,
        legacy.headline,
        legacy.news_details,
        legacy.article_url,
        legacy.published_time,
        legacy.collected_time,
        legacy.story_group_id,
        legacy.generated_summary
    FROM articles_legacy AS legacy
    JOIN newspapers AS newspaper
      ON newspaper.newspaper_name = legacy.newspaper
    """)
    connection.execute("DROP TABLE articles_legacy")

connection.execute("""
INSERT OR IGNORE INTO newspapers (
    newspaper_name, website_url, language
)
VALUES (?, ?, ?)
""", ("Lankadeepa", HOME_URL, "Sinhala"))
connection.execute("""
CREATE INDEX IF NOT EXISTS idx_articles_story_id
ON articles (story_id)
""")

connection.commit()

NEWSPAPER_ID = connection.execute(
    "SELECT newspaper_id FROM newspapers WHERE newspaper_name = ?",
    ("Lankadeepa",)
).fetchone()[0]


# ==================================================
# 3. TIME HELPER
# ==================================================

def sri_lanka_now():
    return datetime.now(SL_TIMEZONE)


# ==================================================
# 4. GET WEBSITE DATE
# ==================================================

def get_website_date(soup):
    date_bar = soup.select_one(
        ".top-info-bar .container > div:first-child"
    )

    if date_bar:
        return date_bar.get_text(" ", strip=True)

    return None


# ==================================================
# 5. GET ARTICLE PUBLICATION TIME
# ==================================================

def get_published_time(article_soup):
    metadata_selectors = [
        ("meta", {"property": "article:published_time"}),
        ("meta", {"name": "date"}),
        ("meta", {"itemprop": "datePublished"})
    ]

    for tag_name, attributes in metadata_selectors:
        tag = article_soup.find(tag_name, attrs=attributes)

        if tag and tag.get("content"):
            return tag["content"]

    time_tag = article_soup.find("time")

    if time_tag:
        return (
            time_tag.get("datetime")
            or time_tag.get_text(" ", strip=True)
        )

    return None


# ==================================================
# 6. GET ARTICLE DETAILS
# ==================================================

def get_article_details(article_soup):
    # Try common content selectors
    selectors = [
        "p.story-teaser",
        ".article-content p",
        ".news-content p"
    ]

    for selector in selectors:
        paragraphs = article_soup.select(selector)

        if paragraphs:
            text = " ".join(
                p.get_text(" ", strip=True)
                for p in paragraphs
                if p.get_text(" ", strip=True)
            )

            if text:
                return text

    return None


# ==================================================
# 7. FIND AND SAVE NEWS
# ==================================================

def fetch_news():
    response = session.get(HOME_URL, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "lxml")

    website_date = get_website_date(soup)

    print("Website date:", website_date or "Not found")

    # Discover links to latest-news articles
    news_links = {}

    for link in soup.find_all("a", href=True):
        href = link["href"]
        headline = link.get_text(" ", strip=True)

        if "/latest_news/" not in href:
            continue

        if not headline:
            continue

        article_url = urljoin(HOME_URL, href)
        article_path = urlparse(article_url).path.rstrip("/")

        # The /latest_news/1 link opens the latest-news listing, not an article.
        if not re.search(r"/latest_news/.+/\d+-\d+$", article_path):
            continue

        # Skip navigation links
        if headline.upper() == "MORE ESENA NEWS":
            continue

        # A dictionary automatically removes duplicate URLs
        news_links[article_url] = headline

    print("News links found:", len(news_links))

    new_articles = 0

    for article_url, headline in news_links.items():

        # Skip articles already stored in SQLite
        existing = connection.execute(
            "SELECT 1 FROM articles WHERE article_url = ?",
            (article_url,)
        ).fetchone()

        if existing:
            continue

        try:
            article_response = session.get(
                article_url,
                timeout=20
            )
            article_response.raise_for_status()
            article_response.encoding = article_response.apparent_encoding

            article_soup = BeautifulSoup(
                article_response.text,
                "lxml"
            )

            # Prefer the full headline from the article page
            heading = article_soup.find("h1")

            if heading:
                headline = heading.get_text(" ", strip=True)

            details = get_article_details(article_soup)
            published_time = get_published_time(article_soup)

        except requests.RequestException as error:
            print("Could not retrieve:", article_url)
            print("Reason:", error)
            continue

        collected_time = sri_lanka_now()

        # Save the article even when its publication date is unknown
        connection.execute("""
            INSERT OR IGNORE INTO articles (
                newspaper_id,
                headline,
                article_text,
                article_url,
                published_time,
                collected_time,
                story_id,
                generated_summary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            NEWSPAPER_ID,
            headline,
            details,
            article_url,
            published_time,
            collected_time.isoformat(),
            None,
            None
        ))

        connection.commit()

        new_articles += 1

        print("\nArticle saved!")
        print("Headline:", headline)
        print("Details:", details or "Details not found")
        print("Published:", published_time or "Date not found")
        print("Collected:", collected_time.isoformat())
        print("URL:", article_url)
        print("-" * 60)

    total = connection.execute(
        "SELECT COUNT(*) FROM articles"
    ).fetchone()[0]

    print("\nNew articles saved:", new_articles)
    print("Total articles in database:", total)


# ==================================================
# 8. CONTINUOUS TRACKING
# ==================================================

try:
    while True:
        print("\n" + "=" * 60)

        print(
            "Checking at:",
            sri_lanka_now().strftime("%Y-%m-%d %H:%M:%S")
        )

        try:
            fetch_news()

        except requests.RequestException as error:
            print("Homepage request failed:", error)

        print(f"\nChecking again in {CHECK_INTERVAL} seconds.")
        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("\nTracking stopped. Database records are preserved.")

finally:
    connection.close()
