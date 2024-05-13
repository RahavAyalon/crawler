from crawler import Crawler
from dotenv import load_dotenv
import os

load_dotenv()

if __name__ == '__main__':
    base_url = os.getenv('BASE_URL')
    crawler = Crawler(base_url=base_url)
    crawler.start()
