from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from queue import Queue, Empty
import threading
import validators
import w3lib.url
import requests
import logging
import random
import os
from concurrent.futures import ThreadPoolExecutor
from time import sleep

from user_agents import user_agents

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class Crawler:
    def __init__(self, base_url: str, max_threads: int = 5):
        if not validators.url(base_url):
            logger.error("Invalid base URL: {}".format(base_url))
            raise ValueError("Invalid base URL")

        parsed_url = urlparse(base_url)
        self.output_folder = parsed_url.netloc.replace('www.', '')

        if not self.output_folder:
            logger.error("Invalid base URL: {}".format(base_url))
            raise ValueError("Invalid base URL")

        if not os.path.exists(self.output_folder):
            os.mkdir(self.output_folder)

        self.base_url = base_url
        self.max_threads = max_threads
        self.lock = threading.Lock()
        self.crawled_urls = set()
        self.urls_to_crawl = Queue()
        self.urls_to_crawl.put(self.base_url)

        self.user_agents = user_agents
        self.retry_attempts = 3
        self.retry_delay = 2

    def fetch(self, url: str):
        headers = {'User-Agent': random.choice(self.user_agents)}
        for attempt in range(self.retry_attempts):
            try:
                response = requests.get(url, headers=headers, timeout=5)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    sleep(self.retry_delay)
                else:
                    logger.error("All retries failed for {}".format(url))
        return None

    def save_page(self, content: str, url: str):
        file_name = f"{urlparse(url).netloc}{urlparse(url).path}".replace('/', '_')
        full_path = os.path.join(self.output_folder, file_name + ".html")
        with open(full_path, 'w', encoding="utf-8") as file:
            file.write(content)

    def queue_url_if_valid(self, url: str):
        if not validators.url(url):
            logger.error("Invalid URL: {}".format(url))
            return

        canonical_url = w3lib.url.canonicalize_url(url)
        with self.lock:
            if canonical_url in self.crawled_urls:
                return
            self.crawled_urls.add(canonical_url)
            return canonical_url

    def worker(self, url: str):
        url_to_crawl = self.queue_url_if_valid(url)
        if not url_to_crawl: return

        html_content = self.fetch(url_to_crawl)
        if not html_content:
            return

        self.save_page(html_content, url_to_crawl)

        soup = BeautifulSoup(html_content, 'html.parser')
        links = soup.find_all('a', href=True)
        for link in links:
            link_url = link.get('href')
            full_url = urljoin(url, link_url)
            if urlparse(self.base_url).netloc.endswith(urlparse(full_url).netloc):
                with self.lock:
                    cur_normalised_url = w3lib.url.canonicalize_url(full_url)
                    if cur_normalised_url not in self.crawled_urls:
                        self.urls_to_crawl.put(cur_normalised_url)

    def start(self):
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            while True:
                try:
                    url = self.urls_to_crawl.get(timeout=10)
                    executor.submit(self.worker, url)
                except Empty:
                    if threading.active_count() > 1:
                        continue
                    break
