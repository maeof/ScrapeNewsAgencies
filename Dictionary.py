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
from os import listdir
from os.path import isfile, join

from datetime import datetime, date, timedelta

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

def main():
    mypath = "C:\Data\deliverables\sources"
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

    wordsDict = {}

    i = 0
    for file in onlyfiles:
        f = open(mypath + "\\" + file, "r", encoding="utf-8")
        content = f.readlines()
        f.close()

        verylong = ""
        for c in content:
            verylong += str(c)

        textContent = cleanPageContent(verylong)

        # reuse scraper to read only the articleScope parts
        translation_table = dict.fromkeys(map(ord, '!@#$%^&?*()_+=[]-;<>/\|~1234567890\,.:"„“'), None)
        textContent = textContent.translate(translation_table)
        textContent = textContent.replace("\n", " ")

        for word in textContent.split(" "):
            if word not in wordsDict:
                wordsDict[word] = 1
            else:
                wordsDict[word] = wordsDict[word] + 1

        i += 1

        if i == 50:
            break

    print(wordsDict)

if __name__ == '__main__':
    main()