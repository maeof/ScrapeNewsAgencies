from LinkScraper import FifteenLinkScraper, DelfiLinkScraper, LrytasLinkScraper
import ScraperHelper as helper

from datetime import date

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


import multiprocessing
from joblib import Parallel, delayed
from tqdm import tqdm

class SimpleLinkScraper:
    def __init__(self, linkScraperStrategy):
        self._linkScraperStrategy = linkScraperStrategy

    def getLinks(self):
        workUrls = self._linkScraperStrategy.getWorkUrls()
        inputs = tqdm(workUrls)

        links = Parallel(n_jobs=self._linkScraperStrategy.getCpuCount())(delayed(self._processUrl)(url) for url in inputs)

        return self._mergeResults(links)

    def _processUrl(self, url):
        pageContent = self._linkScraperStrategy.getPageContent(url)
        linksFromPage = self._linkScraperStrategy.getLinksFromPage(pageContent)
        return linksFromPage

    def _mergeResults(self, setsOfLinks):
        merged = set()
        for eachSet in setsOfLinks:
            merged = merged.union(eachSet)
        return merged

def main():
    workFolder = "C:\Data\GetLinks"
    workSessionFolder = helper.createWorkSessionFolder(workFolder)

    fromDate = date(2019, 1, 1)
    toDate = date(2019, 12, 31)

    fifteenSeedUrl = "https://www.15min.lt/naujienos/aktualu/lietuva"
    fifteenParams = "?offset={0}%2023:59:59" #15min date format: year-month-day

    delfiSeedUrl = "https://www.delfi.lt/archive/index.php"
    delfiParams = "?fromd={0}&tod={1}&channel=1&category=0&query=&page={2}" #delfi date in format: day.month.year
    delfiIterationsCount = 866
    #delfiIterationsCount = 2 #Test

    # Iterations justification: each click on "Daugiau" loads 24 unique articles. We load articles forever and at each 25th
    # load we check the last article's date from it's url - if it's still newer than fromDate - we continue the articles loading.
    # This strategy was set up to work like so because there is no trivial way to access the archive in lrytas.lt portal.
    lrytasSeedUrl = "https://www.lrytas.lt/lietuvosdiena/aktualijos/"
    lrytasWebDriverPath = ChromeDriverManager().install()

    cpuCount = multiprocessing.cpu_count()

    fifteenLinkScraper = SimpleLinkScraper(FifteenLinkScraper(cpuCount, fromDate, toDate, fifteenSeedUrl, fifteenParams))
    fifteenLinks = fifteenLinkScraper.getLinks()
    helper.saveToFile(workSessionFolder, fifteenLinks)

    delfiLinkScraper = SimpleLinkScraper(DelfiLinkScraper(cpuCount, fromDate, toDate, delfiSeedUrl, delfiParams, delfiIterationsCount))
    delfiLinks = delfiLinkScraper.getLinks()
    helper.saveToFile(workSessionFolder, delfiLinks)

    lrytasLinkScraper = SimpleLinkScraper(LrytasLinkScraper(fromDate, toDate, lrytasSeedUrl, lrytasWebDriverPath))
    lrytasLinks = lrytasLinkScraper.getLinks()
    helper.saveToFile(workSessionFolder, lrytasLinks)


if __name__ == '__main__':
    main()