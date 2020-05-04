import abc
import csv

from urllib.parse import urlparse

from GetLinks3 import httpget
from requests import get
from requests.exceptions import RequestException
from contextlib import closing

from bs4 import BeautifulSoup

import os
from datetime import datetime

import multiprocessing
from joblib import Parallel, delayed
from tqdm import tqdm

import re

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


def isResponseOK(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def getCurrentDateTime():
    now = datetime.now()
    return now.strftime("%d_%m_%Y_%H_%M_%S")


def createWorkSessionFolder(createInPath):
    createdFolder = createInPath + "\\" + "session_" + getCurrentDateTime()
    os.mkdir(createdFolder)
    return createdFolder


def validateUrl(url):
    ret = True

    if not str(url).startswith("http") and not str(url).startswith("www"):
        ret = False

    return ret


def cleanPageContent(html):
    soup = BeautifulSoup(html, "html.parser") # create a new bs4 object from the html data loaded
    for script in soup(["script", "style"]): # remove all javascript and stylesheet code
        script.extract()
    # get text
    text = soup.get_text()
    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text


def cleanUrl(url):
    return str(url).strip()


def processUrl(url, outputFolder):
    if not validateUrl(url):
        return

    cleanedUrl = cleanUrl(url)

    pageContent = ""
    pageText = ""
    try:
        pageContent = httpget(cleanedUrl)
        #pageText = cleanPageContent(pageContent)
    except:
        print("{0}: error processing resource {1}".format(os.getpid(), url))
        return

    #allCases = re.findall(r'(skandal.*?\b)', pageText, flags=re.IGNORECASE)

    translation_table = dict.fromkeys(map(ord, '!@#$%^&?*()_+=[];/\\,.:'), None)
    strippedUrl = cleanedUrl.translate(translation_table)[:40]

    outputFileName = outputFolder + "\\" + str(os.getpid()) + "_" + strippedUrl

    #resultFile = open(outputFileName + ".txt", "w+", encoding="utf-8")
    #resultFile.write(("{0}: {1}".format(len(allCases), allCases)))
    #resultFile.close()

    if pageContent is not None:
        pageContentFile = open(outputFileName + ".htm", "w+", encoding="utf-8")
        pageContentFile.writelines(pageContent)
        pageContentFile.close()

class ContentScraperAbstract(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def getArticleDatePublished(self):
        """Required Method"""

    @abc.abstractmethod
    def getArticleDateModified(self):
        """Required Method"""

    @abc.abstractmethod
    def getArticleTitle(self):
        """Required Method"""

    @abc.abstractmethod
    def getArticleCategory(self):
        """Required Method"""

    @abc.abstractmethod
    def getArticleAuthor(self):
        """Required Method"""

    @abc.abstractmethod
    def getArticleAuthorPosition(self):
        """Required Method"""

    @abc.abstractmethod
    def getArticleScope(self):
        """Required Method"""

class FifteenContentScraper(ContentScraperAbstract):
    def __init__(self, url, pageContent):
        self._url = url
        self._pageContent = pageContent
        self._soup = BeautifulSoup(pageContent, "html.parser")

    def getArticleDatePublished(self):
        datePublishedTag = self._soup.find("meta", attrs={"itemprop":"datePublished"})
        datePublished = datePublishedTag.get("content")
        return datePublished

    def getArticleDateModified(self):
        dateModifiedTag = self._soup.find("meta", attrs={"itemprop":"dateModified"})
        dateModified = dateModifiedTag.get("content")
        return dateModified

    def getArticleTitle(self):
        articleTitleTag = self._soup.find("h1", attrs={"itemprop":"headline"})
        articleTitle = articleTitleTag.text.strip()
        return articleTitle

    def getArticleCategory(self):
        categoryTags = self._soup.findAll("li", attrs={"itemprop":"itemListElement"})
        categoryName = ""
        for categoryTag in categoryTags:
            categoryNameTag = categoryTag.find("span", attrs={"itemprop":"name"})

            if len(categoryName) != 0:
                categoryName += " > "
            categoryName += categoryTag.text.strip()

        return categoryName

    def getArticleAuthor(self): #TODO: optimize - only perform find of authorTag once per url, reuse authorTag in getArticleAuthorPosition etc.
        authorTag = self._soup.find("div", attrs={"class":"author-name-block"}) #this tag represents author block if it's 15min employee and the source is 15min
        if authorTag is None:
            authorTag = self._soup.find("div", attrs={"class":"author-info author-text"}) #this tag represents author from another source

        if authorTag is not None:
            authorName = authorTag.find("span", attrs={"itemprop":"name"}).text.strip()
        else:
            authorName = self.getNotFoundValue()

        return authorName

    def getArticleAuthorPosition(self):
        authorTag = self._soup.find("div", attrs={"class":"author-name-block"})
        if authorTag is not None:
            authorPosition = authorTag.find("div", attrs={"class":"author-position"}).text.strip()
        else:
            authorPosition = self.getNotFoundValue()

        return authorPosition

    def getArticleScope(self):
        """Required Method"""

    def getNotFoundValue(self):
        return "n/a"

class SimpleContentScraper:
    def __init__(self, inputFilePath, cpuCount):
        self._inputFilePath = inputFilePath
        self._cpuCount = cpuCount

    def scrape(self):
        fileContent = self.getContentFromInputFile()
        workUrls = tqdm(fileContent)

        results = Parallel(n_jobs=self._cpuCount)(delayed(self.processUrl)(url) for url in workUrls)
        return results

    def processUrl(self, url):
        pageContent = httpget(self.cleanurl(url))

        result = []
        if pageContent is not None:
            contentScraperStrategy = self.getContentScraperStrategy(url, pageContent)
            result.append(contentScraperStrategy.getArticleTitle())
            result.append(contentScraperStrategy.getArticleDatePublished())
            result.append(contentScraperStrategy.getArticleDateModified())
            result.append(contentScraperStrategy.getArticleCategory())
            result.append(contentScraperStrategy.getArticleAuthor())
            result.append(contentScraperStrategy.getArticleAuthorPosition())

        return result

    def getContentScraperStrategy(self, url, pageContent):
        parsedUrl = urlparse(url)
        contentScraperStrategy = ContentScraperAbstract()

        if parsedUrl.hostname == "www.15min.lt":
            contentScraperStrategy = FifteenContentScraper(url, pageContent)
        elif parsedUrl.hostname == "www.delfi.lt":
            raise Exception("Could not pick Delfi content scraper strategy for " + url)
        elif parsedUrl.hostname == "www.lrytas.lt":
            raise Exception("Could not pick LRytas content scraper strategy for " + url)
        else:
            raise Exception("Could not pick content scraper strategy for " + url)

        return contentScraperStrategy

    def getContentFromInputFile(self):
        inputFile = open(self._inputFilePath, "r")
        fileContent = inputFile.readlines()
        inputFile.close()
        return fileContent

    def cleanurl(self, url):
        return str(url).strip()

def main():
    linksFile = "C:\\Data\\AnalyzeLinks\\links.csv"

    workFolder = "C:\Data\AnalyzeLinks"
    workSessionFolder = createWorkSessionFolder(workFolder)
    resultFile = workSessionFolder + "\\" + "result.csv"

    cpuCount = multiprocessing.cpu_count()

    simpleContentScraper = SimpleContentScraper(linksFile, cpuCount)
    scrapeResult = simpleContentScraper.scrape()

    with open(resultFile, "w+", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(scrapeResult)

    #inputFile = open(linksFile, "r")
    #urls = inputFile.readlines()
    #inputFile.close()

    #processedList = Parallel(n_jobs=cpuCount)(delayed(processUrl)(url, workSessionFolder) for url in urls)

    # file = open(linksFile, "r")
    # resultFile = open(resultFile, "w+", encoding="utf-8")
    # for line in file.readlines():
    #     url = line
    #     pageSource = ""
    #     try:
    #         pageSource = httpget(url)
    #     except:
    #         print("Could not get from " + url)
    #
    #     workFileName = "page_" + getCurrentDateTime() + ".htm"
    #     if pageSource is not None:
    #         workFile = open(workSessionFolder + "\\" + workFileName, "w+", encoding="utf-8")
    #         workFile.writelines(pageSource)
    #         workFile.close()
    #
    #     parsedUrl = urlparse(url)
    #
    #     nextSlashPosition = parsedUrl.path.find("/", 1)
    #     category = parsedUrl.path[1:nextSlashPosition]
    #     fullLink = line
    #     wordPosition = parsedUrl.path.find("skandal")
    #
    #     resultFile.write("{0},{1},{2},{3},{4}".format(parsedUrl.netloc, category, wordPosition, fullLink, workFileName))
    #
    # resultFile.close()
    # file.close()


if __name__ == '__main__':
    main()