import random
from robocorp.tasks import task
from robocorp import storage
from robocorp import workitems

import logging
from news_scraper import NewsScraper

# Access the current input work item
item = workitems.inputs.current

search_phrase = item.payload.get("search_phrase")
news_category = item.payload.get("news_category")
num_months = int(item.payload.get("num_months", 0))
scraper = NewsScraper('https://news.google.com', search_phrase, news_category, num_months)

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

    scraper.navigate_to_site()
    scraper.enter_search_phrase()
    scraper.select_news_category()
    scraper.choose_latest_news()

@task
def scrape_news_data():
    scraper.extract_news_data()
    scraper.store_data_in_excel()
    scraper.download_all_news_pictures()

# @task
# def navigate_to_website():
#     scraper.navigate_to_site()

# @task
# def enter_search_phrase():
#     scraper.enter_search_phrase()

# @task
# def select_news_category():
#     scraper.select_news_category()

# @task
# def choose_latest_news():
#     scraper.choose_latest_news()

# @task
# def extract_news_data():
#     scraper.extract_news_data()

# @task
# def store_data_in_excel():
#     scraper.store_data_in_excel()

# @task
# def download_news_picture():
#     scraper.download_news_picture() 

