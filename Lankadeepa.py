import logging
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


NEWSPAPER_NAME = "Lankadeepa"
HOME_URL = "https://www.lankadeepa.lk/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
FETCH_STATS = {"discovered": 0, "failed": 0}
logger = logging.getLogger(__name__)


def _details(soup: BeautifulSoup) -> str | None:
    for selector in (
        "section.article-pages .article-body p",
        ".cat-item-teaser.mb-2 p",
        "p.story-teaser",
        ".article-content p",
        ".news-content p",
    ):
        paragraphs = [
            node.get_text(" ", strip=True)
            for node in soup.select(selector)
        ]
        text = " ".join(value for value in paragraphs if value)
        if text:
            return text
    tag = soup.find("meta", attrs={"property": "og:description"})
    return tag.get("content", "").strip() if tag else None


def _published_time(soup: BeautifulSoup) -> str | None:
    for attributes in (
        {"property": "article:published_time"},
        {"name": "date"},
        {"itemprop": "datePublished"},
    ):
        tag = soup.find("meta", attrs=attributes)
        if tag and tag.get("content"):
            return tag["content"]
    tag = soup.find("time")
    return tag.get("datetime") or tag.get_text(" ", strip=True) if tag else None


def fetch_news() -> list[dict[str, str | None]]:
    FETCH_STATS["discovered"] = 0
    FETCH_STATS["failed"] = 0
    session = requests.Session()
    session.headers.update(HEADERS)
    response = session.get(HOME_URL, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "lxml")
    links: dict[str, str] = {}

    for link in soup.find_all("a", href=True):
        headline = link.get_text(" ", strip=True)
        article_url = urljoin(HOME_URL, link["href"])
        path = urlparse(article_url).path.rstrip("/")
        if (
            headline
            and "/latest_news/" in path
            and re.search(r"/latest_news/.+/\d+-\d+$", path)
        ):
            links[article_url] = headline

    articles = []
    FETCH_STATS["discovered"] = len(links)
    for article_url, headline in links.items():
        try:
            article_response = session.get(article_url, timeout=20)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.text, "lxml")
            heading = article_soup.find("h1")
            articles.append(
                {
                    "headline": (
                        heading.get_text(" ", strip=True)
                        if heading else headline
                    ),
                    "article_text": _details(article_soup),
                    "article_url": article_url,
                    "published_time": _published_time(article_soup),
                }
            )
        except requests.RequestException as error:
            FETCH_STATS["failed"] += 1
            logger.warning("%s: failed article %s: %s", NEWSPAPER_NAME, article_url, error)
    return articles
