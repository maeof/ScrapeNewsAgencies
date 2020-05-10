import ScraperHelper as helper
from ContentFetcher import FileContentFetcher, HttpContentFetcher
from ContentScraper import ContentScraperAbstract, FifteenContentScraper, DelfiContentScraper, LrytasContentScraper

import os
import multiprocessing
from joblib import Parallel, delayed
from tqdm import tqdm

import csv
import re


class SimpleContentScraper:
    def __init__(self, contentFetcherStrategy, workSessionFolder, cpuCount, regexCompliancePatterns):
        self._contentFetcherStrategy = contentFetcherStrategy
        self._workSessionFolder = workSessionFolder
        self._cpuCount = cpuCount
        self._regexCompliancePatterns = regexCompliancePatterns

    def scrape(self):
        workList = tqdm(self._contentFetcherStrategy.getWorkList())

        results = Parallel(n_jobs=self._cpuCount)(delayed(self._processResource)(resource) for resource in workList)

        results.insert(0, self._getDataSetHeader())
        return self._removeEmptyEntries(results)

    def _processResource(self, resource):
        contentScraperStrategy = self.getContentScraperStrategy(self._contentFetcherStrategy.getContentScraperSuggestion(resource), resource)

        pageContent = self._contentFetcherStrategy.getContent(resource)
        result = []
        try:
            if pageContent is not None:
                contentScraperStrategy.createParser(pageContent) #TODO: rename to init
                allMatches = self._getPatternMatches(contentScraperStrategy.getArticleScope())

                if self._isArticleCompliant(allMatches) and contentScraperStrategy.isArticleCompliant():
                    result.append(self._contentFetcherStrategy.getResourceName(resource))
                    result.append(contentScraperStrategy.getArticleTitle())
                    result.append(contentScraperStrategy.getArticleCategory())
                    result.append(contentScraperStrategy.getArticleDatePublished())
                    result.append(contentScraperStrategy.getArticleDateModified())
                    result.append(contentScraperStrategy.getArticleAuthor())
                    result.append(contentScraperStrategy.getArticleAuthorPosition())
                    result = self._getPatternMatchesColumns(result, allMatches)
                    result.append(resource)

                    savedContentFileName = self._savePageContentToFile(resource, pageContent)
                    result.append(savedContentFileName)
        except Exception as ex:
            result.clear()
            print(str(os.getpid()) + " failed to process: " + resource)
            self._log(ex, resource)

        return result

    def _removeEmptyEntries(self, entries):
        cleanedEntries = [x for x in entries if x != []]
        return cleanedEntries

    def _getDataSetHeader(self):
        dataSetHeader = ["Source", "Title", "Category", "Date published", "Date modified", "Author", "Author position"]
        for pattern in self._regexCompliancePatterns:
            dataSetHeader.append("Count of {0}".format(pattern))
        dataSetHeader.append("Url")
        dataSetHeader.append("Path to local source")
        return dataSetHeader

    def _savePageContentToFile(self, resource, pageContent):
        resourceName = self._contentFetcherStrategy.getFullSafeResourceName(resource)

        outputFileName = self._workSessionFolder + "\\" + str(os.getpid()) + "_" + helper.getCurrentDateTime() + resourceName + ".htm"

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
            logFile.write(str(os.getpid()) + " tried to process it at " + str(helper.getCurrentDateTime()) + " but failed." + "\n\n")
            logFile.close()
        except:
            print("lol failed to write to the log file but please do continue: " + url)

    def _getPatternMatchesColumns(self, currentResult, allPatternMatches):
        for i in range(0, len(self._regexCompliancePatterns)):
            count = 0
            for matches in allPatternMatches[i]:
                count += len(matches)
            currentResult.append(count)
        return currentResult

    @staticmethod
    def getContentScraperStrategy(suggestion, resource):
        contentScraperStrategy = ContentScraperAbstract()

        if suggestion == "www.15min.lt":
            contentScraperStrategy = FifteenContentScraper(resource)
        elif suggestion == "www.delfi.lt":
            contentScraperStrategy = DelfiContentScraper(resource)
        elif suggestion == "www.lrytas.lt":
            contentScraperStrategy = LrytasContentScraper(resource, "c:\\data\\chromedriver\\chromedriver.exe")
        else:
            raise Exception("Could not pick content scraper strategy for " + resource)

        return contentScraperStrategy

    def _getPatternMatches(self, articleScopes):
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

    def _isArticleCompliant(self, allMatches):
        isCompliant = False

        for i in range(0, len(self._regexCompliancePatterns)):
            for matches in allMatches[i]:
                if len(matches) > 0:
                    isCompliant = True
                    break

        return isCompliant

def main():
    linksFile = "C:\\Data\\AnalyzeLinks\\links.csv"
    linksFile = "C:\\Data\\AnalyzeLinks\\linksTest.csv" #Test

    workFolder = "C:\Data\AnalyzeLinks"
    workSessionFolder = helper.createWorkSessionFolder(workFolder)
    resultFile = workSessionFolder + "\\" + "result.csv"

    filesPathFileContentFetcher = "C:\Data\deliverables\iteration3\sources"
    filesPathFileContentFetcher = workSessionFolder #Test

    cpuCount = multiprocessing.cpu_count()
    #cpuCount = 1 #Test
    regexCompliancePatterns = [r"(skandal.*?\b)"]

    simpleContentScraper = SimpleContentScraper(HttpContentFetcher(linksFile), workSessionFolder, cpuCount, regexCompliancePatterns)
    scrapeResult = simpleContentScraper.scrape()

    simpleContentScraper = SimpleContentScraper(FileContentFetcher(filesPathFileContentFetcher), workSessionFolder, cpuCount, regexCompliancePatterns)
    scrapeResult = simpleContentScraper.scrape()

    with open(resultFile, "w+", encoding="utf-8", newline='') as resultFile:
        writer = csv.writer(resultFile)
        writer.writerows(scrapeResult)


if __name__ == '__main__':
    main()