import logging
import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
import json
import hashlib
from elasticsearch import Elasticsearch

# configure logging. debug is loud, info is less loud, error is bad stuff only.
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("simple-scraping-example")

# you will need to fill this stuff out to get the program to function
url = ''
elasticHost = ''
indexName = 'dev_scrape'
pushoverToken = ''
pushoverKey = ''
sleepDuration = 300


# set the user agent header to a real browser
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}

# set initial hash to none, so we don't accidentally send a notification the first time we check it
lastHash = None

# create Elasticsearch object
es = Elasticsearch(hosts=elasticHost)
# create index if it doesn't exist already, ignore a 400 error which indicates that it does already
es.indices.create(index=indexName, ignore=400)

# create a class for the date you intend to scrape. this makes converting to JSON much easier
class ShopState:
    def __init__(self, timestamp, isOpen, contentHash):
        self.timestamp = timestamp
        self.isOpen = isOpen
        self.contentHash = contentHash

def sendPushoverNotification(message):
    try:
        r = requests.post("https://api.pushover.net/1/messages.json", data = {"token": pushoverToken, "user": pushoverKey, "message": message})
    except requests.exceptions.RequestException as e:
        logger.error("error sending pushover notification: {}".format(e)) 

# main loop
while True:
    # set the current timestamp to now
    checkTime = datetime.utcnow().isoformat()

    # make the request to the page
    try:
        response = requests.get(url, headers=headers)
        # parse the downloaded homepage
        soup = BeautifulSoup(response.text, "lxml")
        # hash the content from the div class=paragraph objects.
        # you will likely have to adjust this to a different HTML attribute, depending on the content you are trying to scrape
        # this hash is useful to validate whether the content changed or not, since we are really only looking for specific strings
        # in general you should build in failsafes, because regex isn't always reliable, and web content changes a lot
        contentHash = hashlib.sha256(str(soup.findAll('div',attrs={"class":"paragraph"})).encode('utf-8')).hexdigest()
        # compare lasthash to current hash, then send a notification if it changes
        if (lastHash is not None) and (contentHash != lastHash):
            sendPushoverNotification("site content changed, check {}".format(url))
        # set the last hash to the current hash, so we can compare it next time.
        lastHash = contentHash

        # search for strings in the content with regex.
        # if the string is found at least once, we assume the books are closed 
        if len(soup.findAll(string=re.compile("books closed", re.IGNORECASE))) > 0:
            isOpen = False
        # if the string isn't found at least once, let's check if the books are open
        elif len(soup.findALL(string=re.compile("books open", re.IGNORECASE))) > 0:
            isOpen = True
        # if neither string is found, either the website is down or the content of the page has changed enough that we need to rework our logic, so we exit
        else:
            # send notification so we know that something went wrong
            sendPushoverNotification("Something is up, scraper exiting, check {}".format(url))
            sys.exit("couldn't determine state, exiting")

        # now that we have data, let's do something with it
        currentState = ShopState(checkTime, isOpen, contentHash)
        # log the actual json info (optional)
        logger.info("{}".format(json.dumps(currentState.__dict__)))
        # index to elasticsearch
        try:
            es.index(index=indexName,body=json.dumps(currentState.__dict__))
        except Exception as e:
            logger.error("error indexing to elasticsearch: {}".format(e))

    except Exception as e:
        logger.error('error in main loop: {}'.format(e))
        continue

    # sleep for the interval specified (default 5 minutes)
    time.sleep(sleepDuration)
