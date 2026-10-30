import logging
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


NEWSPAPER_NAME = "Hiru News"
HOME_URL = "https://www.hirunews.lk/"
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
        path = urlparse(article_url).path.rstrip("/")
        if re.fullmatch(r"/\d+/[^/]+", path):
            headline = link.get_text(" ", strip=True)
            if headline:
                links[article_url] = headline

    articles = []
    FETCH_STATS["discovered"] = len(links)
    for article_url, headline in links.items():
        try:
            article_response = session.get(article_url, timeout=20)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.text, "lxml")
            content = article_soup.select_one(
                "section.single_news .head-content + div"
            )
            text = content.get_text(" ", strip=True) if content else None
            if text:
                text = re.sub(r"^Share Post\s*", "", text, flags=re.I)
            heading = article_soup.find("h1")
            articles.append(
                {
                    "headline": (
                        _meta(article_soup, "og:title")
                        or (heading.get_text(" ", strip=True) if heading else headline)
                    ),
                    "article_text": text or _meta(article_soup, "og:description"),
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
