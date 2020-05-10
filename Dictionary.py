import ScraperHelper as helper
from AnalyzeLinks import SimpleContentScraper
from ContentFetcher import FileContentFetcher
from ContentScraper import FifteenContentScraper, DelfiContentScraper, LrytasContentScraper

from bs4 import BeautifulSoup

import multiprocessing
from joblib import Parallel, delayed
from tqdm import tqdm


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


def createDictionary(work, fetcher):
    scraper = SimpleContentScraper.getContentScraperStrategy(fetcher.getContentScraperSuggestion(work), work)
    scraper.createParser(fetcher.getContent(work))
    articleScopes = scraper.getArticleScope()

    wordsDict = {}

    text = ""
    for scope in articleScopes:
        try:
            text += " " + scope.text
        except:
            text += " " + scope

    translation_table = dict.fromkeys(map(ord, '!@#$%^&?*()_+=[]-;<>/\|~1234567890\,.:"„“'), None)
    text = text.translate(translation_table)
    text = text.replace("\n", " ")
    text = text.replace("\t", "")
    text = text.replace("–", " ")
    text = text.strip()

    for word in text.split(" "):
        word = word.strip()

        if len(word) == 0:
            continue

        if word not in wordsDict:
            wordsDict[word] = 1
        else:
            wordsDict[word] = wordsDict[word] + 1

    return wordsDict


def processWork(work, fetcher):
    wordsDict = {}
    try:
        wordsDict = createDictionary(work, fetcher)
    except Exception as ex:
        print("Could not process, exception caught: " + str(ex))
    return wordsDict


def main():
    mypath = "C:\Data\deliverables\iteration3\sources"
    #mypath = "C:\Data\AnalyzeLinks\session_10_05_2020_17_48_14" #Test
    dictionariesPath = "C:\Data\Dictionary"
    cpuCount = multiprocessing.cpu_count()

    fetcher = FileContentFetcher(mypath)
    workList = tqdm(fetcher.getWorkList())

    wordDictionaries = Parallel(n_jobs=cpuCount)(delayed(processWork)(work, fetcher) for work in workList)

    wordDict = {}
    for dictionary in wordDictionaries:
        for key in dictionary:
            if key not in wordDict:
                wordDict[key] = dictionary[key]
            else:
                wordDict[key] = wordDict[key] + dictionary[key]

    dictFileName = dictionariesPath + "\\" + "dictionary_" + helper.getCurrentDateTime() + ".csv"
    resultFile = open(dictFileName, "w+", encoding="utf-8")
    for key in wordDict:
        resultFile.write(key + "," + str(wordDict[key]) + "\n")
    resultFile.close()

if __name__ == '__main__':
    main()