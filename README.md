## Repo Overview
This is a simple example of a web scraping script, designed to accompany my Source Zero Con talk which happened on May 27th, 2021 at 13:00 Eastern Time. A recording of the talk is available at [https://youtu.be/nSqzyd-nDcY](https://youtu.be/nSqzyd-nDcY)

## Script Overview
I built this script to scrape a tattoo artist's web page, determine if their books are open or closed, and store the results in a json object. It also notifies me using pushover if the web content changes, the program exits, or if the books are determined to be open.

Although this script is not really intended to be used outside of an example, it can do the following:
* Scrape a page using requests
* Extract paragraph divs with BeautifulSoup
* Generate hash of the paragraph content with hashlib
* Use regex to determine if books are open or closed
* Create json object with relevant attributes, including timestamp, content hash, and book state
* Index JSON object to Elasticsearch Index
* Depending on results, send push notification using [Pushover](https://pushover.net)
 * the script will notify the user if the content hash changes, if the books are open or if there is an error causing the script to exit.

## Usage
```sh
git clone https://github.com/cham423/simple-scraping-example
pip3 install -r requirements.txt
```
fill out required parameters, including:
* url to scrape
* elasticHost - the Elasticsearch Endpoint to Log to 
* indexName - the index created to store all the results records
* pushoverToken - your pushover app token
* pushoverKey - your pushover user key

```sh
python3 scrape.py
```

## Limitations
* This script is designed for one very specific use case, scraping [this](https://www.jaxntheboxtattoos.com/) page
* The script is not really modular, everything runs in a while loop
* Error handling is pretty limited 
