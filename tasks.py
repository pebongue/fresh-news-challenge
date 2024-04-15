from robocorp import browser
from robocorp.tasks import task

import logging
from news_scraper import NewsScraper


@task
def scrap_fresh_news():
    """
    Solve the RPA Fresh-News challenge
    
    Automate the process of extracting data from a news site.
    """
    browser.configure(
        browser_engine="chromium",
        screenshot="only-on-failure",
        headless=False,
    )
    try:
        logging.basicConfig(level=logging.INFO)

        scraper = NewsScraper("https://news.yahoo.com", "Israel")
        scraper.run()

    finally:
        # Place for teardown and cleanups
        # NewsScraper handles browser closing
        print('Done')