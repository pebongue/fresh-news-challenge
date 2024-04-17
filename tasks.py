from random import random
from robocorp import browser
from robocorp.tasks import task
from robocorp import storage
from robocorp import workitems

import logging
from news_scraper import NewsScraper

scraper = NewsScraper('https://news.yahoo.com', 'Israel')

def clean_list(list_of_strings):
    keyword_content_list = list_of_strings.strip().split("\n")
    trimmed_list = [string.strip() for string in keyword_content_list]
    cleaned_list = [string for string in trimmed_list if string]
    return cleaned_list

@task
def retrieve_website_to_scrape():
    websites = clean_list(storage.get_text('websites_to_scrape'))
    print(websites)
    workitems.outputs.create(payload={"website": random.choice(websites)})

@task
def navigate_to_website():
    scraper.navigate_to_site()

@task
def enter_search_phrase():
    scraper.enter_search_phrase()

@task
def select_news_category():
    scraper.select_news_category()

@task
def choose_latest_news():
    scraper.choose_latest_news()

@task
def extract_news_data():
    scraper.extract_news_data()

@task
def store_data_in_excel():
    scraper.store_data_in_excel()

@task
def download_news_picture():
    scraper.download_news_picture()

