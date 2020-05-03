import abc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

import multiprocessing
from joblib import Parallel, delayed
from tqdm import tqdm

#chrome_options = Options()
#chrome_options.add_argument("--headless")

#service = Service('c:\\data\\chromedriver\\chromedriver.exe')
#service.start()
#cdi = webdriver.Chrome("c:\\data\\chromedriver\\chromedriver.exe", options=chrome_options)
#cdi = webdriver.Remote(service.service_url)

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import urllib3 as urllib
from urllib.parse import urlparse
import sys
import os
from datetime import datetime, date, timedelta

def getCurrentDateTime():
    now = datetime.now()
    return now.strftime("%d_%m_%Y_%H_%M_%S")

def createWorkSessionFolder(createInPath):
    createdFolder = createInPath + "\\" + "session_" + getCurrentDateTime()
    os.mkdir(createdFolder)
    return createdFolder

def httpget(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if isResponseOK(resp):
                return resp.text
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None

def httpget2(url):
    cdi.get(url)
    time.sleep(3)
    return cdi.page_source

def isResponseOK(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)

def getIncrementalUrl(url, i):
    return url.replace("{0}", str(i))

def isIncrementalUrl(url):
    if (url.find("{0}") != -1):
        return True
    else:
        return False

def getLinksFromPageContent(pageContent):
    soup = BeautifulSoup(pageContent, 'html.parser')
    links = set()

    for a in soup.find_all('a'):
        url = a.get('href')
        links.add(url)

    return links

def saveToFile(path, links):
    fileNameWithPath = path + "\\" + "result.csv"
    file = open(fileNameWithPath, "a+")
    for link in links:
        if (link is not None):
            file.write(link + "\n")
    file.close()

def getLinks(regularUrls):
    allLinks = set()
    for url in regularUrls:
        pageContent = httpget(url)
        links = getLinksFromPageContent(pageContent)
        allLinks = allLinks.union(links)

    saveToFile(workSessionFolder, allLinks)

def getLinksFromIncrementalUrls(incrementalUrls, pagesCount):
    allLinks = set()
    for url in incrementalUrls:
        for i in range(1, pagesCount + 1):
            urlForRequest = getIncrementalUrl(url, i)

            print(urlForRequest)

            startTime = time.time()
            pageContent = httpget(urlForRequest)
            endTime = time.time()
            print("httpget: {0}".format(endTime - startTime))

            startTime = time.time()
            links = getLinksFromPageContent(pageContent)
            endTime = time.time()
            print("getLinksFromPageContent: {0}".format(endTime - startTime))

            startTime = time.time()
            allLinks = allLinks.union(links)
            print("allLinks.union(links): {0}".format(endTime - startTime))
            endTime = time.time()

    saveToFile(workSessionFolder, allLinks)

def validateArgs(args):
    if (args[1] is None or args[2] is None):
        print("Wrong arguments. 1st argument is the file of links, 2nd argument is the incremental value of how many pages to view.")
        return False

class LinkScraperAbstract(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def getWorkUrls(self):
        """Required Method"""

    @abc.abstractmethod
    def formatDate(self, date):
        """Required Method"""

    @abc.abstractmethod
    def getIterationsCount(self):
        """Required Method"""

    @abc.abstractmethod
    def getLinksFromPage(self, pageContent):
        """Required Method"""

class FifteenLinkScraper(LinkScraperAbstract):
    def __init__(self, fromDate, toDate, seedUrl, params):
        self._fromDate = fromDate
        self._toDate = toDate
        self._seedUrl = seedUrl
        self._params = params

    def getWorkUrls(self):
        workUrls = []
        iterationsCount = self.getIterationsCount()

        for i in range(0, iterationsCount):
            url = self._seedUrl
            newDate = self._toDate - timedelta(i)
            urlParams = str(self._params).format(self.formatDate(newDate))
            url += urlParams
            workUrls.append(url)

        return workUrls

    def formatDate(self, date = date(2000, 1, 1)):
        return date.strftime("%Y-%m-%d")

    def getIterationsCount(self):
        dateDelta = self._toDate - self._fromDate
        iterationsCount = dateDelta.days
        iterationsCount += 1
        return iterationsCount

    def getLinksFromPage(self, pageContent):
        soup = BeautifulSoup(pageContent, 'html.parser')
        links = set()

        for article in soup.findAll("article"):
            for a in article.findAll("a", attrs={"class":"vl-img-container"}):
                links.add(a.get('href'))

        return links

class DelfiLinkScraper(LinkScraperAbstract):
    def __init__(self, fromDate, toDate, seedUrl, params, iterationsCount = 0):
        self._fromDate = fromDate
        self._toDate = toDate
        self._seedUrl = seedUrl
        self._params = params
        self._iterationsCount = iterationsCount

    def getWorkUrls(self):
        workUrls = []
        iterationsCount = self.getIterationsCount()

        fromDateText = self.formatDate(self._fromDate)
        toDateText = self.formatDate(self._toDate)

        for i in range(1, iterationsCount):
            url = self._seedUrl
            urlParams = str(self._params).format(fromDateText, toDateText, i)
            url += urlParams
            workUrls.append(url)

        return workUrls

    def formatDate(self, date=date(2000, 1, 1)):
        return date.strftime("%d.%m.%Y")

    def getIterationsCount(self):
        return self._iterationsCount + 1

    def getLinksFromPage(self, pageContent):
        soup = BeautifulSoup(pageContent, 'html.parser')
        links = set()

        for div in soup.findAll("div", attrs={"class":"row"}):
            for a in div.findAll("a", attrs={"class":"img-link"}):
                links.add(a.get('href'))

        return links

class SimpleLinkScraper:
    def __init__(self, linkScraperStrategy):
        self._linkScraperStrategy = linkScraperStrategy

    def processUrl(self, url):
        pageContent = httpget(url)
        linksFromPage = self.getLinksFromPage(pageContent)
        return linksFromPage

    def getLinks(self, cpuCount):
        workUrls = self.getWorkUrls()
        inputs = tqdm(workUrls)

        links = Parallel(n_jobs=cpuCount)(delayed(self.processUrl)(url) for url in inputs)

        return self.mergeResults(links)

    def mergeResults(self, setsOfLinks):
        merged = set()
        for eachSet in setsOfLinks:
            merged = merged.union(eachSet)
        return merged

    def getWorkUrls(self):
        return self._linkScraperStrategy.getWorkUrls()

    def getLinksFromPage(self, pageContent):
        return self._linkScraperStrategy.getLinksFromPage(pageContent)

def main(args):
    workFolder = "C:\Data\GetLinks"
    workSessionFolder = createWorkSessionFolder(workFolder)

    fromDate = date(2019, 1, 1)
    #toDate = date(2019, 12, 31)
    toDate = date(2019, 12, 31)

    fifteenSeedUrl = "https://www.15min.lt/naujienos/aktualu/lietuva"
    fifteenParams = "?offset={0}%2023:59:59" #15min date format: year-month-day

    delfiSeedUrl = "https://www.delfi.lt/archive/index.php"
    delfiParams = "?fromd={0}&tod={1}&channel=1&category=0&query=&page={2}" #delfi date in format: day.month.year
    delfiIterationsCount = 866

    #fifteenLinkScraper = SimpleLinkScraper(FifteenLinkScraper(fromDate, toDate, fifteenSeedUrl, fifteenParams))
    #fifteenLinks = fifteenLinkScraper.getLinks(multiprocessing.cpu_count())
    #saveToFile(workSessionFolder, fifteenLinks)

    delfiLinkScraper = SimpleLinkScraper(DelfiLinkScraper(fromDate, toDate, delfiSeedUrl, delfiParams, delfiIterationsCount))
    delfiLinks = delfiLinkScraper.getLinks(multiprocessing.cpu_count())
    saveToFile(workSessionFolder, delfiLinks)

    #print(b.instanceMethod())

    # linksFilePath = "links.txt"
    # pagesCount = 10
    #
    # file = open(linksFilePath, "r")
    # fileLines = file.readlines()
    # file.close()
    #
    # incrementalUrls = []
    # regularUrls = []
    #
    # for line in fileLines:
    #     if (isIncrementalUrl(line)):
    #         incrementalUrls.append(line)
    #     else:
    #         regularUrls.append(line)
    #
    # getLinksFromIncrementalUrls(incrementalUrls, pagesCount)
    # #getLinks(regularUrls)
    #

if __name__ == '__main__':
    main(sys.argv)