from pathlib import Path
import requests
from robocorp import workitems
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from RPA.Browser.Selenium import Selenium
import pandas as pd
import logging
import os
import re

from tenacity import retry

class NewsData:
    def __init__(self, title, date, description, picture_url):
        self.title = title
        self.date = date
        self.description = description
        self.picture_url = picture_url
        self.picture_filename = None

    def count_search_phrases(self, search_phrase):
        return self.title.count(search_phrase) + self.description.count(search_phrase)

    def contains_money(self):
        pattern = r"\$\d+(\.\d{1,2})?|\d+ dollars|\d+ USD"
        return bool(re.search(pattern, self.title)) or bool(re.search(pattern, self.description))

class NewsScraper:
    def __init__(self, base_url, search_phrase, news_category, num_months):
        self.browser = Selenium()
        self.base_url = base_url
        self.search_phrase = search_phrase
        self.news_data = []
        self.news_category = news_category
        self.num_months = num_months
        self.logger = logging.getLogger(__name__)

    INPUT_XPATH = "xpath=//input[@name='p']"

    @retry(stop=3, wait=2000)
    def navigate_to_site(self):
        try:
            self.browser.set_download_directory(os.getcwd())
            self.browser.open_available_browser(self.base_url)
            self.browser.wait_until_page_contains_element(self.INPUT_XPATH, timeout=30)
        except Exception as e:
            self.logger.error(f"Error navigating to site: {e}")
            raise
    
    @retry(stop=3, wait=2000)
    def enter_search_phrase(self):
        try:
            self.browser.input_text("xpath=//input[@name='p']", self.search_phrase)
            self.browser.press_keys("xpath=//input[@name='p']", "\\13")  # Press Enter key
            self.browser.wait_until_page_contains_element("xpath=//div[contains(@class,'NewsArticle')]", timeout=30)
        except Exception as e:
            self.logger.error(f"Error entering search phrase: {e}")
            raise

    @retry(stop=3, wait=2000)
    def select_news_category(self):
        if self.news_category:
            try:
                self.browser.click_link(self.news_category)
            except Exception as e:
                self.logger.error(f"Error selecting news category: {e}")
                raise
    
    @retry(stop=3, wait=2000)
    def choose_latest_news(self):
        try:
            self.browser.click_link("Latest")
        except Exception as e:
            self.logger.error(f"Error choosing latest news: {e}")
            raise
    
    def validate_data(self, title, date, description, picture_url):
        if any(not var for var in [title, date, description, picture_url]):
            raise ValueError("Invalid data extracted")

    @retry(stop=3, wait=2000)
    def extract_news_data(self):
        try:
            self.browser.wait_until_element_is_visible("css:div.NewsArticle__content")
            news_elements = self.browser.find_elements("css:div.NewsArticle__content")
            for news in news_elements:
                title = self.browser.find_element("css:h4", parent=news).text
                date = self.browser.find_element("css:time", parent=news).get_attribute("datetime")
                description = self.browser.find_element("css:p", parent=news).text
                picture_url = self.browser.find_element("css:img", parent=news).get_attribute("src")
                self.validate_data(title, date, description, picture_url)
                self.news_data.append(NewsData(title, date, description, picture_url))
        except Exception as e:
            self.logger.error(f"Error extracting news data: {e}")
            raise

    def store_data_in_excel(self):
        try:
            data = []
            for nd in self.news_data:
                data.append({
                    'title': nd.title,
                    'date': nd.date,
                    'description': nd.description,
                    'picture_url': nd.picture_url,
                    'count_search_phrase': nd.count_search_phrases(self.search_phrase),
                    'contains_money': nd.contains_money()
                })
            df = pd.DataFrame(data)
            df.to_excel("news_data.xlsx", index=False)
            self.logger.info("Data extracted and saved successfully.")
        except Exception as e:
            self.logger.error(f"Error storing data in excel: {e}")
            raise

    @retry(stop=3, wait=2000)
    def download_news_picture(self, news_data):
        try:
            response = requests.get(news_data.picture_url)
            if response.status_code == 200:
                filename = Path(news_data.picture_url).name
                with open(filename, 'wb') as f:
                    f.write(response.content)
                news_data.picture_filename = filename
            else:
                self.logger.error(f"Failed to download picture: HTTP status code: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Error downloading news picture: {e}")
            raise

    def download_all_news_pictures(self):
        for nd in self.news_data:
            self.download_news_picture(nd)

    def run(self):
        try:
            self.navigate_to_site()
            self.enter_search_phrase()
            self.select_news_category()
            self.choose_latest_news()
            self.extract_news_data()
            self.store_data_in_excel()
            self.download_all_news_pictures()
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            self.browser.close_all_browsers()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Access the current input work item
    item = workitems.inputs.current
    print(item)

    if item is not None and item.payload is not None:
        search_phrase = item.payload.get("search_phrase")
        news_category = item.payload.get("news_category")
        num_months = int(item.payload.get("num_months", 0))

        scraper = NewsScraper("https://news.yahoo.com", search_phrase, news_category, num_months)
        scraper.run()
