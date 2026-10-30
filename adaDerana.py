import logging
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


NEWSPAPER_NAME = "Ada Derana"
HOME_URL = "https://sinhala.adaderana.lk/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
FETCH_STATS = {"discovered": 0, "failed": 0}
logger = logging.getLogger(__name__)


def _meta(soup: BeautifulSoup, property_name: str) -> str | None:
    tag = soup.find("meta", attrs={"property": property_name})
    return tag.get("content", "").strip() if tag else None


def fetch_news() -> list[dict[str, str | None]]:
    FETCH_STATS["discovered"] = 0
    FETCH_STATS["failed"] = 0
    session = requests.Session()
    session.headers.update(HEADERS)
    response = session.get(HOME_URL, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    links: dict[str, str] = {}

    for link in soup.find_all("a", href=True):
        article_url = urljoin(HOME_URL, link["href"])
        if not re.fullmatch(r"/news/\d+", urlparse(article_url).path.rstrip("/")):
            continue
        card = link.select_one("div.w-2\\/3")
        headline_node = card.select_one("span.font-semibold") if card else None
        headline = headline_node.get_text(" ", strip=True) if headline_node else ""
        if headline:
            links[article_url] = headline

    articles = []
    FETCH_STATS["discovered"] = len(links)
    for article_url, headline in links.items():
        try:
            article_response = session.get(article_url, timeout=20)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.text, "lxml")
            article = article_soup.select_one("article")
            paragraphs = (
                article.select("p") if article else []
            )
            text = " ".join(
                dict.fromkeys(
                    node.get_text(" ", strip=True)
                    for node in paragraphs
                    if node.get_text(" ", strip=True)
                )
            ) or _meta(article_soup, "og:description")
            articles.append(
                {
                    "headline": _meta(article_soup, "og:title") or headline,
                    "article_text": text,
                    "article_url": article_url,
                    "published_time": _meta(
                        article_soup, "article:published_time"
                    ),
                }
            )
        except requests.RequestException as error:
            FETCH_STATS["failed"] += 1
            logger.warning("%s: failed article %s: %s", NEWSPAPER_NAME, article_url, error)
    return articles
