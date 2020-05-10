import abc

import csv

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
from os import listdir
from os.path import isfile, join

from datetime import datetime, date, timedelta

from AnalyzeLinks import ContentFetcherAbstract
from AnalyzeLinks import FileContentFetcher

from AnalyzeLinks import SimpleContentScraper
from AnalyzeLinks import FifteenContentScraper
from AnalyzeLinks import DelfiContentScraper
from AnalyzeLinks import LrytasContentScraper

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

def processWork(work, fetcher):
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

    for word in text.split(" "):
        if len(word) == 0:
            continue

        if word not in wordsDict:
            wordsDict[word] = 1
        else:
            wordsDict[word] = wordsDict[word] + 1

    return wordsDict

def getCurrentDateTime():
    now = datetime.now()
    return now.strftime("%d_%m_%Y_%H_%M_%S")

def main():
    mypath = "C:\Data\deliverables\iteration3\sources"
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

    with open(dictionariesPath + "\\" + "dictionary_" + getCurrentDateTime(), "w+", encoding="utf-8", newline='') as resultFile:
        writer = csv.writer(resultFile)
        writer.writerows(wordDict)

if __name__ == '__main__':
    main()