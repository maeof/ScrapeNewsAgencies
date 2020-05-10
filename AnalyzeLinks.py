import abc
import csv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from urllib.parse import urlparse

from GetLinks3 import httpget
from requests import get
from requests.exceptions import RequestException
from contextlib import closing

from bs4 import BeautifulSoup
import json

import os
from datetime import datetime
from datetime import date
import time

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

    if resp.status_code != 200:
        saveToFile("C:\Data\AnalyzeLinks", [resp.status_code, resp.url])

    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def saveToFile(path, links):
    fileNameWithPath = path + "\\" + "loghttperrcodes.txt"
    file = open(fileNameWithPath, "a+")
    for link in links:
        if link:
            file.write(str(link) + "\n")
    file.close()

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

    allCases = re.findall(r'(skandal.*?\b)', pageText, flags=re.IGNORECASE)

    translation_table = dict.fromkeys(map(ord, '!@#$%^&?*()_+=[];/\\,.:'), None)
    strippedUrl = cleanedUrl.translate(translation_table)[:40]

    outputFileName = outputFolder + "\\" + str(os.getpid()) + "_" + strippedUrl

    if pageContent is not None:
        pageContentFile = open(outputFileName + ".htm", "w+", encoding="utf-8")
        pageContentFile.writelines(pageContent)
        pageContentFile.close()

    #resultFile = open(outputFileName + ".txt", "w+", encoding="utf-8")
    #resultFile.write(("{0}: {1}".format(len(allCases), allCases)))
    #resultFile.close()

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

    @abc.abstractmethod
    def getNotFoundValue(self):
        """Required Method"""

    @abc.abstractmethod
    def isArticleCompliant(self):
        """Required Method"""

    @abc.abstractmethod
    def getPageContent(self, resourceLink):
        """Required Method"""

    @abc.abstractmethod
    def createParser(self, pageContent):
        """Required Method"""

class FifteenContentScraper(ContentScraperAbstract):
    def __init__(self, url):
        self._url = url

    def getArticleDatePublished(self):
        datePublishedTag = self._soup.find("meta", attrs={"itemprop":"datePublished"})

        datePublished = None
        if datePublishedTag:
            datePublished = datePublishedTag.get("content")

        return datePublished

    def getArticleDateModified(self):
        dateModifiedTag = self._soup.find("meta", attrs={"itemprop":"dateModified"})

        dateModified = None
        if dateModifiedTag:
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
        articleTitleTag = self._soup.find("h1", attrs={"itemprop":"headline"})
        articleIntroTag = self._soup.find("h4", attrs={"class":"intro"})
        articleContentTag = self._soup.find("div", attrs={"class": "article-content"})

        scopes = [articleTitleTag, articleIntroTag, articleContentTag]
        return scopes

    def getNotFoundValue(self):
        return "n/a"

    def isArticleCompliant(self):
        return True

    def getPageContent(self, resourceLink):
        return httpget(resourceLink)

    def createParser(self, pageContent):
        self._pageContent = pageContent
        self._soup = BeautifulSoup(pageContent, "html.parser")

class DelfiContentScraper(ContentScraperAbstract):
    def __init__(self, url):
        self._url = url

    def getArticleDatePublished(self):
        datePublishedTag = self._soup.find("div", attrs={"class":"source-date"})
        if (datePublishedTag is None):
            datePublishedTag = self._soup.find("div", attrs={"class":"delfi-source-date"})

        datePublished = ""
        if datePublishedTag is not None:
            datePublished = datePublishedTag.text.strip()
        else:
            datePublished = None

        return datePublished

    def getArticleDateModified(self):
        dateModified = None
        return dateModified

    def getArticleTitle(self):
        articleTitle = self._getRegularArticleTitle()

        if len(articleTitle) == 0:
            articleTitle = self._getMultimediaArticleTitle()

        if len(articleTitle) == 0:
            articleTitle = self.getNotFoundValue()

        return articleTitle

    def _getRegularArticleTitle(self):
        articleTitleTag = self._soup.find("div", attrs={"class": "article-title"})

        articleTitle = ""
        if articleTitleTag is not None:
            articleTitle = articleTitleTag.find("h1").text.strip()
            articleTitle = articleTitle.replace("\n", " ")
            articleTitle = articleTitle.replace("\t", "")

        return articleTitle

    def _getMultimediaArticleTitle(self):
        articleTitleTag = self._soup.find("h1", attrs={"itemprop": "headline"})

        articleTitle = ""
        if articleTitleTag is not None:
            articleTitle = articleTitleTag.text.strip()
            articleTitle = articleTitle.replace("\n", " ")
            articleTitle = articleTitle.replace("\t", "")

        return articleTitle

    def getArticleCategory(self):
        categoryName = ""

        categoryFatherTag = self._soup.find("div", attrs={"class":"delfi-breadcrumbs delfi-category-location"})
        if categoryFatherTag is not None:
            categoryTags = categoryFatherTag.findAll("span", attrs={"itemprop":"itemListElement"})

        if categoryTags is not None:
            for categoryTag in categoryTags:
                if len(categoryName) != 0:
                    categoryName += " > "
                categoryName += categoryTag.text.strip()

        if len(categoryName) == 0:
            categoryName = self.getNotFoundValue()

        return categoryName

    def getArticleAuthor(self):
        authorTag = self._soup.find("div", attrs={"class":"delfi-author-name"})
        if authorTag is None:
            authorTag = self._soup.find("div", attrs={"class":"delfi-source-name"})

        if authorTag is not None:
            authorName = authorTag.text.strip()
        else:
            authorName = self.getNotFoundValue()

        return authorName

    def getArticleAuthorPosition(self):
        authorTag = self._soup.find("div", attrs={"class":"delfi-author-name"})

        authorPosition = ""
        if authorTag is not None:
            authorBioLinkTag = authorTag.find("a")
            if authorBioLinkTag is not None:
                authorBioLink = authorBioLinkTag.get("href")
                bioPageContent = httpget(authorBioLink)

                if bioPageContent is not None:
                    babySoup = BeautifulSoup(bioPageContent, "html.parser")
                    authorPosition = babySoup.find("div", attrs={"class":"title"}).text.strip()

                    if len(authorPosition) == 0:
                        authorPosition = self.getNotFoundValue()
        else:
            authorPosition = self.getNotFoundValue()

        return authorPosition

    def getArticleScope(self):
        articleTitleTag = self._soup.find("div", attrs={"class":"article-title"})
        articleIntroTag = self._soup.find("div", attrs={"class":"delfi-article-lead"})

        bigColumnTag = self._soup.find("div", attrs={"class": "col-xs-8"})
        articleContentTag = bigColumnTag.find("div") #or bigColumnTag.div (finds the first <div> in bigColumnTag because delfi

        scopes = [articleTitleTag, articleIntroTag, articleContentTag]
        return scopes

    def getNotFoundValue(self):
        return "n/a"

    def isArticleCompliant(self):
        return True

    def getPageContent(self, resourceLink):
        return httpget(resourceLink)

    def createParser(self, pageContent):
        self._pageContent = pageContent
        self._soup = BeautifulSoup(pageContent, "html.parser")

class LrytasContentScraper(ContentScraperAbstract):
    def __init__(self, url, webDriverPath):
        self._url = url
        self._webDriverPath = webDriverPath

    def getArticleDatePublished(self):
        datePublishedTag = self._soup.find("meta", attrs={"itemprop":"datePublished"})

        datePublished = None
        if datePublishedTag:
            datePublished = datePublishedTag.get("content")

        return datePublished

    def getArticleDateModified(self):
        dateModified = None
        return dateModified

    def getArticleTitle(self):
        articleTitle = self.getNotFoundValue()

        aboutBlockJson = self._soup.find("script", type="application/ld+json").contents
        if aboutBlockJson:
            jsonText = aboutBlockJson[0]
            jsonText = jsonText.strip().replace("\t", "").replace("\n", "").replace("\r", "")
            jsonText = self._cleanHtml(jsonText)
            about = json.loads(jsonText)
            articleTitle = about["headline"].strip()

        return articleTitle

    def _cleanHtml(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

    def getArticleCategory(self):
        categoryName = ""
        aboutBlockJson = self._soup.findAll("script", attrs={"type": "application/ld+json"})[-1].contents

        if aboutBlockJson:
            jsonText = aboutBlockJson[0]
            jsonText = jsonText.strip().replace("\t", "").replace("\n", "").replace("\r", "")
            jsonText = self._cleanHtml(jsonText)
            about = json.loads(jsonText)
            for itemListElement in about["itemListElement"]:
                if len(categoryName) != 0:
                    categoryName += " > "
                categoryName += itemListElement["item"]["name"]

        if len(categoryName) == 0:
            categoryName = self.getNotFoundValue()

        return categoryName

    def getArticleAuthor(self):
        authorName = self.getNotFoundValue()

        aboutBlockJson = self._soup.find("script", type="application/ld+json").contents
        if aboutBlockJson:
            jsonText = aboutBlockJson[0]
            jsonText = jsonText.strip().replace("\t", "").replace("\n", "").replace("\r", "")
            jsonText = self._cleanHtml(jsonText)
            about = json.loads(jsonText)
            authorName = about["publisher"]["name"]

        return authorName

    def getArticleAuthorPosition(self):
        return self.getNotFoundValue()

    def getArticleScope(self):
        script = self._soup.find("body").find("script").contents[0]
        script = script.strip().replace("\t", "").replace("\n", "")
        script = self._cleanHtml(script)

        pos = script.find("{")
        pos2 = script.find("\r")

        jsonbby = script[pos:pos2 - 1]

        articleJsonObj = json.loads(jsonbby)

        scopes = [articleJsonObj["clearContent"], articleJsonObj["title"]]
        return scopes

    def getNotFoundValue(self):
        return "n/a"

    def isArticleCompliant(self):
        isCompliant = True
        articleDate = self._getArticleDate()

        if articleDate and (articleDate < date(2019, 1, 1) or articleDate > date(2019, 12, 31)):
            isCompliant = False

        return isCompliant

    def _getArticleDate(self):
        url = self._url
        parsedUrl = urlparse(url)

        sectorPosition = 0
        pathParts = parsedUrl.path[1:].split("/")
        articleDate = None
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
                    articleDate = date(year, month, day)
                except:
                    articleDate = None

                break

            sectorPosition += 1

        return articleDate

    def getPageContent(self, resourceLink):
        time.sleep(1)
        return httpget(resourceLink)

    def createParser(self, pageContent):
        self._pageContent = pageContent
        self._soup = BeautifulSoup(pageContent, "html.parser")

class SimpleContentScraper:
    def __init__(self, inputFilePath, workSessionFolder, cpuCount, regexCompliancePatterns):
        self._inputFilePath = inputFilePath
        self._workSessionFolder = workSessionFolder
        self._cpuCount = cpuCount
        self._regexCompliancePatterns = regexCompliancePatterns

    def scrape(self):
        fileContent = self.getContentFromInputFile() #TODO: strategies: cache, web
        fileContent = self.filterFile(fileContent)
        workUrls = tqdm(fileContent)

        results = Parallel(n_jobs=self._cpuCount)(delayed(self.processUrl)(url) for url in workUrls)
        results.insert(0, self.getDataSetHeader())
        return self.removeEmptyEntries(results)

    def filterFile(self, fileContent):
        doNotIncludeTheseLinksPlease = ["video", "multimedija"]
        filteredFileContent = []
        for url in fileContent:
            parsedUrl = urlparse(url)
            firstPathInUrl = parsedUrl.path[1:parsedUrl.path.find("/", 1)]
            if firstPathInUrl in doNotIncludeTheseLinksPlease:
                continue
            filteredFileContent.append(url)
        return filteredFileContent

    def removeEmptyEntries(self, entries):
        cleanedEntries = [x for x in entries if x != []]
        return cleanedEntries

    def getDataSetHeader(self):
        dataSetHeader = ["Source", "Title", "Category", "Date published", "Date modified", "Author", "Author position"]
        for pattern in self._regexCompliancePatterns:
            dataSetHeader.append("Count of {0}".format(pattern))
        dataSetHeader.append("Url")
        dataSetHeader.append("Path to local source")
        return dataSetHeader

    def processUrl(self, url):
        cleanUrl = self.cleanurl(url)
        contentScraperStrategy = self.getContentScraperStrategy(url)

        # TODO: strategies: cache, web. for cache read file, for web GET
        pageContent = contentScraperStrategy.getPageContent(cleanUrl)
        result = []
        try:
            if pageContent is not None:
                contentScraperStrategy.createParser(pageContent) #TODO: rename to init
                allMatches = self.getPatternMatches(contentScraperStrategy.getArticleScope())

                if self.isArticleCompliant(allMatches) and contentScraperStrategy.isArticleCompliant():
                    result.append(self.getSourceHostname(cleanUrl))
                    result.append(contentScraperStrategy.getArticleTitle())
                    result.append(contentScraperStrategy.getArticleCategory())
                    result.append(contentScraperStrategy.getArticleDatePublished())
                    result.append(contentScraperStrategy.getArticleDateModified())
                    result.append(contentScraperStrategy.getArticleAuthor())
                    result.append(contentScraperStrategy.getArticleAuthorPosition())
                    result = self.getPatternMatchesColumns(result, allMatches)
                    result.append(cleanUrl)

                    savedContentFileName = self._savePageContentToFile(cleanUrl, pageContent)
                    result.append(savedContentFileName)
        except Exception as ex:
            result.clear()
            print(str(os.getpid()) + " failed to process: " + url)
            self._log(ex, cleanUrl)

        return result

    def _getCurrentDateTime(self):
        now = datetime.now()
        return now.strftime("%Y_%m_%d_%H_%M_%S")

    def _savePageContentToFile(self, url, pageContent):
        parsedUrl = urlparse(url)

        translationTable = dict.fromkeys(map(ord, '!@#$%^&?*()_+=[];/\\,.:'), None)
        strippedPath = parsedUrl.path.translate(translationTable)[:40]

        strippedHostname = parsedUrl.hostname.replace("w", "").replace(".", "")
        safeUrl = strippedHostname + "_" + strippedPath

        outputFileName = self._workSessionFolder + "\\" + str(os.getpid()) + "_" + self._getCurrentDateTime() + safeUrl + ".htm"

        pageContentFile = open(outputFileName, "w+", encoding="utf-8")
        pageContentFile.writelines(pageContent)
        pageContentFile.close()

        return outputFileName

    def _log(self, exception, url):
        try:
            logFile = open(self._workSessionFolder + "\\" + "log.txt", "a+")
            logFile.write("Exception has occured: " + str(url) + "\n")
            logFile.write(str(exception) + "\n")
            logFile.write(str(exception.args) + "\n")
            logFile.write(str(os.getpid()) + " tried to process it at " + str(self._getCurrentDateTime()) + " but failed." + "\n\n")
            logFile.close()
        except:
            print("lol failed to write to the log file but please do continue: " + url)

    def getSourceHostname(self, url):
        return urlparse(url).hostname

    def getPatternMatchesColumns(self, currentResult, allPatternMatches):
        for i in range(0, len(self._regexCompliancePatterns)):
            count = 0
            for matches in allPatternMatches[i]:
                count += len(matches)
            currentResult.append(count)
        return currentResult

    def getContentScraperStrategy(self, url):
        parsedUrl = urlparse(url)
        contentScraperStrategy = ContentScraperAbstract()

        if parsedUrl.hostname == "www.15min.lt":
            contentScraperStrategy = FifteenContentScraper(url)
        elif parsedUrl.hostname == "www.delfi.lt":
            contentScraperStrategy = DelfiContentScraper(url)
        elif parsedUrl.hostname == "www.lrytas.lt":
            contentScraperStrategy = LrytasContentScraper(url, "c:\\data\\chromedriver\\chromedriver.exe")

            #pid = os.getpid()
            #if pid not in globalCdiCache:
                #chrome_options = Options()
                #chrome_options.add_argument("--headless")
                #cdi = webdriver.Chrome("c:\\data\\chromedriver\\chromedriver.exe", options=chrome_options)
                #globalCdiCache[pid] = cdi
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

    def getPatternMatches(self, articleScopes):
        allMatches = []
        for pattern in self._regexCompliancePatterns:
            matches = []
            for scope in articleScopes:
                try:
                    scopeText = scope.text
                except:
                    scopeText = str(scope)
                matches.append(re.findall(pattern, scopeText, flags=re.IGNORECASE))

            allMatches.append(matches)

        return allMatches

    def isArticleCompliant(self, allMatches):
        isCompliant = False

        for i in range(0, len(self._regexCompliancePatterns)):
            for matches in allMatches[i]:
                if len(matches) > 0:
                    isCompliant = True
                    break

        return isCompliant

class ContentFetcherAbstract(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def getContent(self, resource):
        """Required Method"""

class FileContentFetcher(ContentFetcherAbstract):
    def __init__(self):
        self._a = 1

    def getContent(self, resource):
        return

class HttpContentFetcher(ContentFetcherAbstract):
    def __init__(self):
        self._a = 1

    def getContent(self, resource):
        return self._get(resource)

    def _get(self, url):
        """
        Attempts to get the content at `url` by making an HTTP GET request.
        If the content-type of response is some kind of HTML/XML, return the
        text content, otherwise return None.
        """
        try:
            with closing(get(url, stream=True)) as resp:
                if self._isResponseOK(resp):
                    return resp.text
                else:
                    return None

        except RequestException as e:
            print(str(e))
            return None

    def _isResponseOK(self, resp):
        """
        Returns True if the response seems to be HTML, False otherwise.
        """
        content_type = resp.headers['Content-Type'].lower()

        if resp.status_code != 200:
            saveToFile("C:\Data\AnalyzeLinks", [resp.status_code, resp.url])

        return (resp.status_code == 200
                and content_type is not None
                and content_type.find('html') > -1)

def main():
    linksFile = "C:\\Data\\AnalyzeLinks\\links.csv"

    workFolder = "C:\Data\AnalyzeLinks"
    workSessionFolder = createWorkSessionFolder(workFolder)
    resultFile = workSessionFolder + "\\" + "result.csv"

    cpuCount = multiprocessing.cpu_count()
    #cpuCount = 1
    regexCompliancePatterns = [r"(skandal.*?\b)"]

    simpleContentScraper = SimpleContentScraper(linksFile, workSessionFolder, cpuCount, regexCompliancePatterns)
    scrapeResult = simpleContentScraper.scrape()

    with open(resultFile, "w+", encoding="utf-8", newline='') as resultFile:
        writer = csv.writer(resultFile)
        writer.writerows(scrapeResult)

    #for eachCdi in globalCdiCache:
        #if eachCdi:
            #eachCdi.quit()

if __name__ == '__main__':
    main()