## Overview ##

Given an entry point for a website (e.g.https://example.com), this crawler downloads all pages of the website into a 
designated local folder once.

## Getting Started ##

### Prerequisites ###
- **pip**

### Setup ###

1. Install the project's dependencies:
```bash
pip install -r requirements.txt
```
2. Create an env file in the root folder according to the .env.example file
```bash
touch .env
vi .env
```
3. Run the program:
```bash
python3 main.py
```

### Tests Setup ###

The package contains basic pytest tests for the crawler (unit tests). To setup and run:

1. Install the project's dev-dependencies:
```bash
pip install -r dev-requirements.txt
```
2. Run the tests:
```bash
pytest test_crawler.py
```

## Design ##

#### Main Elements ###

1. **URL Manager:** 
   - Manages the queue of URLs to be crawled (urls_to_crawl)
   - Avoids revisiting URLs by keeping a set of crawled URLs (crawled_urls)
   - Filters and normalizes URLs to ensure they are canonical and within the target domain.
2. **Fetcher:**
   - Downloads web pages using the requests library. 
   - Implements retry logic to handle request failures. 
   - Uses random user-agent headers from a predefined list to avoid request blocking.
3. **Parser:**
   - Parses the HTML content of the web pages to extract links using BeautifulSoup 
   - Submits new links to the URL Manager to be added to the crawl queue.
4. **Storage Manager:**
   - Saves downloaded pages to the filesystem in a specified output directory.
   - Constructs filenames based on URLs to ensure uniqueness.
      Potential Bottlenecks:
5. **Threading and Concurrency:**
   - Uses a ThreadPoolExecutor for managing worker threads that perform the crawling tasks.
   - Handles synchronization issues such as race conditions using a lock when accessing shared resources (crawled URLs
     set).
6. **Logging and Monitoring:**
   - Logs errors and important system events using Python’s logging module. 
   - Provides visibility into the system's operation and helps diagnose issues.

#### Scaling ####

When scaling a web crawler vertically (crawling websites with many unique URLs) 
and horizontally (crawling many websites simultaneously), several issues and mitigation strategies arise:

**Vertical Scaling Issues:**

1. **Long response times:** is currently mitigated by multi-threading which allows crawling various pages in parallel. 
The number of threads can be adjusted based on server and network capacity. 
Future improvement may include auto-scaling of the server's resources when crawling big websites.

2. **Rate limits:** imposed by websites to prevent excessive access is currently managed by the implementation of a 
random delay (between 0.05s to 0.15s) between requests. This feature helps the system to avoid triggering IP block 
mechanisms. The system also utilizes random user-agent request headers to mimic network from different sources. 
Future improvements may include user-agent rotation which will enhance its abilities or even the incorporation of a 
designated service for managing rotating proxy servers or VPNs. Moreover, integrating support for obeying robots.txt 
rules may prevent accessing disallowed links and blocking. 


**Horizontal Scaling Issues:**

1.**Load distribution:** can address challenges of load imbalance where some crawlers might be overburdened. 
To mitigate this issue, we may want to utilize advanced load-balancing techniques that consider each crawler's load and
capacity.

2.**State management:** that maintains consistent state information across crawlers, could be achieved by designing
the system to be stateless where feasible (meaning minimizing the mutual context of different crawlers).
Furthermore, we may want to ensure each website (or part of it) is assigned to only one crawler at a time. 
This can be managed through a centralized queue system that assigns websites (or sub-websites) to crawlers.

3.**Data management:** in a distributed web crawler implemented using local storage can lead to significant scalability
challenges, including limited storage capacity, inconsistency as well as complications in data retrieval for analysis. 
Transitioning to a centralized storage solution, such as a cloud-based storage service like Amazon S3, can address these
issues by offering enhanced scalability, improved data consistency, and simplified management.

#### Loops ####

The crawler avoids loops by maintaining a set of already crawled URLs. Before a URL is processed, it is checked against 
this set. If it has already been processed, it is skipped. This effectively prevents the crawler from revisiting the 
same page. This data structure is suitable as membership checks in sets (like hashmaps) are done in O(1) time complexity.

#### Single Crawl Per Page ####

The system handles multiple URLs pointing to the same page by normalizing URLs to a canonical form before processing,
as well as maintaining a crawled urls set, utilized to make sure the same url is not visited more than once. 
This normalization includes stripping session IDs, sorting query parameters, etc., ensuring that different URLs pointing
to the same content are recognized as such and processed only once.

#### Termination ####

The system finishes downloading all pages when the URL queue is empty and there are no active worker threads. 
This is checked after a timeout period where no new URLs are added to the queue.
