import abc

from urllib.parse import urlparse

from requests import get
from requests.exceptions import RequestException
from contextlib import closing

from os import listdir
from os.path import isfile, join


class ContentFetcherAbstract(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def getWorkList(self):
        """Required Method"""

    @abc.abstractmethod
    def getContentScraperSuggestion(self, resource):
        """Required Method"""

    @abc.abstractmethod
    def getContent(self, resource):
        """Required Method"""

    @abc.abstractmethod
    def getResourceName(self, resource):
        """Required Method"""

    @abc.abstractmethod
    def getFullSafeResourceName(self, resource):
        """Required Method"""


class FileContentFetcher(ContentFetcherAbstract):
    def __init__(self, filesPath):
        self._filesPath = filesPath

    def getWorkList(self):
        onlyFiles = [self._filesPath + "\\" + f for f in listdir(self._filesPath) if isfile(join(self._filesPath, f))]
        return onlyFiles

    def getContentScraperSuggestion(self, resource):
        contentScraperSuggestion = ""

        if resource.find("15minlt") != -1:
            contentScraperSuggestion = "www.15min.lt"
        elif resource.find("delfilt") != -1:
            contentScraperSuggestion = "www.delfi.lt"
        elif resource.find("lrytaslt") != -1:
            contentScraperSuggestion = "www.lrytas.lt"
        else:
            raise Exception("Could not pick content scraper strategy for " + url)

        return contentScraperSuggestion

    def getContent(self, resource):
        resourceFile = open(resource, "r", encoding="utf-8")
        fileContent = resourceFile.readlines()
        mergedFileContent = self._getMergedFileContent(fileContent)
        return mergedFileContent

    def getResourceName(self, resource):
        return self.getContentScraperSuggestion(resource)

    def getFullSafeResourceName(self, resource):
        return self._getFullSafeResourceName(resource)

    def _getFullSafeResourceName(self, resource):
        translationTable = dict.fromkeys(map(ord, '!@#$%^&?*()_+=[];/\\,.:'), None)
        stripped = resource.translate(translationTable)[:40]

        safeUrl = stripped
        return safeUrl

    def _getMergedFileContent(self, fileContent):
        mergedFileContent = ""

        for line in fileContent:
            mergedFileContent += str(line)

        return mergedFileContent


class HttpContentFetcher(ContentFetcherAbstract):
    def __init__(self, inputFilePath):
        self._inputFilePath = inputFilePath

    def getWorkList(self):
        return self._getContentFromInputFile()

    def getContentScraperSuggestion(self, resource):
        return self._getContentScraperSuggestion(resource)

    def getResourceName(self, resource):
        return self._getSourceHostname(resource)

    def getContent(self, resource):
        return self._httpget(resource)

    def getFullSafeResourceName(self, resource):
        return self._getFullSafeResourceName(resource)

    def _getFullSafeResourceName(self, url):
        parsedUrl = urlparse(url)
        translationTable = dict.fromkeys(map(ord, '!@#$%^&?*()_+=[];/\\,.:'), None)
        strippedPath = parsedUrl.path.translate(translationTable)[:40]

        strippedHostname = parsedUrl.hostname.replace("w", "").replace(".", "")
        safeUrl = strippedHostname + "_" + strippedPath
        return safeUrl

    def _getSourceHostname(self, url):
        return urlparse(url).hostname

    def _getContentScraperSuggestion(self, url):
        parsedUrl = urlparse(url)
        contentScraperSuggestion = ""

        if parsedUrl.hostname == "www.15min.lt":
            contentScraperSuggestion = "www.15min.lt"
        elif parsedUrl.hostname == "www.delfi.lt":
            contentScraperSuggestion = "www.delfi.lt"
        elif parsedUrl.hostname == "www.lrytas.lt":
            contentScraperSuggestion = "www.lrytas.lt"
        else:
            raise Exception("Could not pick content scraper strategy for " + url)

        return contentScraperSuggestion

    def _getContentFromInputFile(self):
        inputFile = open(self._inputFilePath, "r")
        fileContent = inputFile.readlines()
        inputFile.close()

        fileContent = self._filterFile(fileContent)

        fileContentCleansed = []
        for line in fileContent:
            fileContentCleansed.append(self._cleanurl(line))

        return fileContentCleansed

    def _filterFile(self, fileContent):
        doNotIncludeTheseLinksPlease = ["video", "multimedija"]
        filteredFileContent = []
        for url in fileContent:
            parsedUrl = urlparse(url)
            firstPathInUrl = parsedUrl.path[1:parsedUrl.path.find("/", 1)]
            if firstPathInUrl in doNotIncludeTheseLinksPlease:
                continue
            filteredFileContent.append(url)
        return filteredFileContent

    def _cleanurl(self, url):
        return str(url).strip()

    def _httpget(self, url):
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
        content_type = resp.headers['Content-Type'].lower()

        if resp.status_code != 200:
            saveToFile("C:\Data\AnalyzeLinks", [resp.status_code, resp.url])

        return (resp.status_code == 200
                and content_type is not None
                and content_type.find('html') > -1)