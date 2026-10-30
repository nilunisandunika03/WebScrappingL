import logging
import time
from datetime import datetime, timedelta, timezone

import Lankadeepa
import Hirunews
import adaDerana
from create_database import create_database
from database import (
    count_articles,
    get_connection,
    get_newspaper_id,
    save_article,
)


CHECK_INTERVAL = 60
SL_TIMEZONE = timezone(timedelta(hours=5, minutes=30))
COLLECTORS = (Lankadeepa, adaDerana, Hirunews)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def collect_once() -> None:
    create_database()
    connection = get_connection()
    try:
        for collector in COLLECTORS:
            name = collector.NEWSPAPER_NAME
            discovered = inserted = updated = duplicates = failed = 0
            newspaper_id = None
            logger.info("Collecting %s", name)
            try:
                articles = collector.fetch_news()
                stats = getattr(collector, "FETCH_STATS", {})
                discovered = stats.get("discovered", len(articles))
                failed = stats.get("failed", 0)
                newspaper_id = get_newspaper_id(connection, name)
                for article in articles:
                    try:
                        result = save_article(
                            connection,
                            newspaper_id,
                            article,
                            datetime.now(SL_TIMEZONE).isoformat(),
                        )
                        if result == "inserted":
                            inserted += 1
                        elif result == "updated":
                            updated += 1
                        else:
                            duplicates += 1
                    except (KeyError, TypeError, ValueError):
                        failed += 1
                        logger.exception("%s: invalid article shape", name)
            except Exception:
                failed += 1
                logger.exception("%s collector failed", name)
            logger.info(
                "%s: discovered=%d inserted=%d updated=%d duplicates=%d "
                "failed=%d total=%d",
                name,
                discovered,
                inserted,
                updated,
                duplicates,
                failed,
                count_articles(connection, newspaper_id)
                if newspaper_id is not None
                else 0,
            )
    finally:
        connection.close()


def main() -> None:
    try:
        while True:
            collect_once()
            logger.info("Next collection in %d seconds", CHECK_INTERVAL)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Collection stopped.")


if __name__ == "__main__":
    main()
