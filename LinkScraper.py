import abc

from datetime import date, timedelta
import time

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import ScraperHelper as helper

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
        return helper.httpget(resourceLink)

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
        return helper.httpget(resourceLink)

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
                time.sleep(1)
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