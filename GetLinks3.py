import abc

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import time

import multiprocessing
from joblib import Parallel, delayed
from tqdm import tqdm

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
    def getLinksFromPage(self, pageContent):
        """Required Method"""

    @abc.abstractmethod
    def getPageContent(self, resourceLink):
        """Required Method"""

    @abc.abstractmethod
    def getCpuCount(self):
        """Required Method"""

class FifteenLinkScraper(LinkScraperAbstract):
    def __init__(self, cpuCount, fromDate, toDate, seedUrl, params):
        self._cpuCount = cpuCount
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

    def getPageContent(self, resourceLink):
        return httpget(resourceLink)

    def getCpuCount(self):
        return self._cpuCount

class DelfiLinkScraper(LinkScraperAbstract):
    def __init__(self, cpuCount, fromDate, toDate, seedUrl, params, iterationsCount = 0):
        self._cpuCount = cpuCount
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

    def getPageContent(self, resourceLink):
        return httpget(resourceLink)

    def getCpuCount(self):
        return self._cpuCount

class LrytasLinkScraper(LinkScraperAbstract):
    def __init__(self, fromDate, toDate, seedUrl, webDriverPath):
        self._fromDate = fromDate
        self._toDate = toDate
        self._seedUrl = seedUrl
        self._webDriverPath = webDriverPath

    def getWorkUrls(self):
        workUrls = []
        workUrls.append(self._seedUrl)
        return workUrls

    def getIterationsCount(self):
        return self._iterationsCount

    def getLinksFromPage(self, pageContent):
        soup = BeautifulSoup(pageContent, 'html.parser')
        links = set()

        if soup:
            for article in soup.findAll("article", attrs={"class":"post"}):
                articleLinkTag = article.find("a")
                if articleLinkTag:
                    articleLink = articleLinkTag.get("href")
                    if self._isLinkValid(articleLink):
                        links.add(articleLink)

        return links

    def getPageContent(self, resourceLink):
        chrome_options = Options()
        #chrome_options.add_argument("--headless")
        cdi = webdriver.Chrome(self._webDriverPath, options=chrome_options)

        loadMoreElement = (By.ID, "loadMore")
        cdi.get(resourceLink)
        timesLoaded = 1

        pageContent = None
        try:
            continueLoading = True
            while continueLoading:
                WebDriverWait(cdi, 10).until(EC.element_to_be_clickable(loadMoreElement)).click()
                timesLoaded += 1

                if (timesLoaded % 25) == 0:
                    partialPageContent = cdi.page_source
                    continueLoading = self._continueLoading(partialPageContent)

            pageContent = cdi.page_source
        except Exception as ex:
            print("Exception has occured on iteration " + str(timesLoaded) + ": " + str(ex))

        cdi.quit()

        return pageContent

    def _continueLoading(self, pageContent):
        continueLoading = True

        soup = BeautifulSoup(pageContent, 'html.parser')
        lastArticleTag = soup.findAll("article", attrs={"class":"post"})[-1]
        lastArticleLinkTag = lastArticleTag.find("a")

        lastArticleDate = None

        if lastArticleLinkTag:
            url = lastArticleLinkTag.get("href")
            parsedUrl = urlparse(url)

            sectorPosition = 0
            pathParts = parsedUrl.path[1:].split("/")
            for sector in pathParts:
                try:
                    value = int(sector)
                except:
                    value = 0

                if value != 0:
                    year = value
                    try:
                        month = int(pathParts[sectorPosition + 1])
                        day = int(pathParts[sectorPosition + 2])
                        lastArticleDate = date(year, month, day)
                    except:
                        lastArticleDate = None

                    break

                sectorPosition += 1

        if lastArticleDate and lastArticleDate < self._fromDate:
            continueLoading = False

        if lastArticleDate:
            print("Currently on date: " + str(lastArticleDate))

        return continueLoading

    def _isLinkValid(self, link):
        isValid = True

        if len(link) == 0 or link is None:
            isValid = False

        return isValid

    def getCpuCount(self):
        return 1

class SimpleLinkScraper:
    def __init__(self, linkScraperStrategy):
        self._linkScraperStrategy = linkScraperStrategy

    def processUrl(self, url):
        pageContent = self._linkScraperStrategy.getPageContent(url)
        linksFromPage = self._linkScraperStrategy.getLinksFromPage(pageContent)
        return linksFromPage

    def getLinks(self):
        workUrls = self._linkScraperStrategy.getWorkUrls()
        inputs = tqdm(workUrls)

        links = Parallel(n_jobs=self._linkScraperStrategy.getCpuCount())(delayed(self.processUrl)(url) for url in inputs)

        return self.mergeResults(links)

    def mergeResults(self, setsOfLinks):
        merged = set()
        for eachSet in setsOfLinks:
            merged = merged.union(eachSet)
        return merged

def main(args):
    workFolder = "C:\Data\GetLinks"
    workSessionFolder = createWorkSessionFolder(workFolder)

    fromDate = date(2019, 1, 1)
    toDate = date(2019, 12, 31)

    fifteenSeedUrl = "https://www.15min.lt/naujienos/aktualu/lietuva"
    fifteenParams = "?offset={0}%2023:59:59" #15min date format: year-month-day

    delfiSeedUrl = "https://www.delfi.lt/archive/index.php"
    delfiParams = "?fromd={0}&tod={1}&channel=1&category=0&query=&page={2}" #delfi date in format: day.month.year
    delfiIterationsCount = 866

    # Iterations justification: each click on "Daugiau" loads 24 unique articles. We load articles forever and at each 25th
    # load we check the last article's date from it's url - if it's still newer than fromDate - we continue the articles loading.
    # This strategy was set up to work like so because there is no trivial way to access the archive in lrytas.lt portal.
    lrytasSeedUrl = "https://www.lrytas.lt/lietuvosdiena/aktualijos/"
    lrytasWebDriverPath = "c:\\data\\chromedriver\\chromedriver.exe"

    cpuCount = multiprocessing.cpu_count()

    #fifteenLinkScraper = SimpleLinkScraper(FifteenLinkScraper(cpuCount, fromDate, toDate, fifteenSeedUrl, fifteenParams))
    #fifteenLinks = fifteenLinkScraper.getLinks()
    #saveToFile(workSessionFolder, fifteenLinks)

    #delfiLinkScraper = SimpleLinkScraper(DelfiLinkScraper(cpuCount, fromDate, toDate, delfiSeedUrl, delfiParams, delfiIterationsCount))
    #delfiLinks = delfiLinkScraper.getLinks()
    #saveToFile(workSessionFolder, delfiLinks)

    lrytasLinkScraper = SimpleLinkScraper(LrytasLinkScraper(fromDate, toDate, lrytasSeedUrl, lrytasWebDriverPath))
    lrytasLinks = lrytasLinkScraper.getLinks()
    saveToFile(workSessionFolder, lrytasLinks)

if __name__ == '__main__':
    main(sys.argv)