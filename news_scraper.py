from pathlib import Path
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
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
    def __init__(self, base_url, search_phrase):
        self.driver = webdriver.Chrome()
        self.base_url = base_url
        self.search_phrase = search_phrase
        self.news_data = []
        self.logger = logging.getLogger(__name__)

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def navigate_to_site(self):
        try:
            self.driver.get(self.base_url)
        except Exception as e:
            self.logger.error(f"Error navigating to site: {e}")
            raise
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def enter_search_phrase(self):
        try:
            search_field = self.driver.find_element(By.NAME, "q")
            search_field.send_keys(self.search_phrase)
            search_field.send_keys(Keys.RETURN)
        except Exception as e:
            self.logger.error(f"Error entering search phrase: {e}")
            raise

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def select_news_category(self):
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "News"))).click()
        except Exception as e:
            self.logger.error(f"Error selecting news category: {e}")
            raise
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def choose_latest_news(self):
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "Latest"))).click()
        except Exception as e:
            self.logger.error(f"Error choosing latest news: {e}")
            raise
    
    def validate_data(self, title, date, description, picture_url):
        if any(not var for var in [title, date, description, picture_url]):
            raise ValueError("Invalid data extracted")

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def extract_news_data(self):
        try:
            news_elements = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.NewsArticle__content")))
            for news in news_elements:
                title = news.find_element(By.CSS_SELECTOR, "h4").text
                date = news.find_element(By.CSS_SELECTOR, "time").get_attribute("datetime")
                description = news.find_element(By.CSS_SELECTOR, "p").text
                picture_url = news.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
                self.validate_data(title, date, description, picture_url)
                self.news_data.append(NewsData(title, date, description, picture_url))
        except Exception as e:
            self.logger.error(f"Error extracting news data: {e}")
            raise

    def store_data_in_excel(self):
        try:
            df = pd.DataFrame([vars(nd) for nd in self.news_data])
            df.to_excel("news_data.xlsx", index=False)
        except Exception as e:
            self.logger.error(f"Error storing data in excel: {e}")
            raise

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def download_news_picture(self, news_data):
        try:
            response = requests.get(news_data.picture_url)
            filename = Path(news_data.picture_url).name
            with open(filename, 'wb') as f:
                f.write(response.content)
            news_data.picture_filename = filename
        except Exception as e:
            self.logger.error(f"Error downloading news picture: {e}")
            raise

    def run(self):
        try:
            self.navigate_to_site()
            self.enter_search_phrase()
            self.select_news_category()
            self.choose_latest_news()
            self.extract_news_data()
            self.store_data_in_excel()
            for nd in self.news_data:
                self.download_news_picture(nd)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            self.driver.quit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    scraper = NewsScraper("https://news.yahoo.com", "Israel")
    scraper.run()