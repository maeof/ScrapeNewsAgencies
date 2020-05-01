from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

chrome_options = Options()
chrome_options.add_argument("--headless")

#service = Service('c:\\data\\chromedriver\\chromedriver.exe')
#service.start()
cdi = webdriver.Chrome("c:\\data\\chromedriver\\chromedriver.exe", options=chrome_options)
#cdi = webdriver.Remote(service.service_url)

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import urllib3 as urllib
from urllib.parse import urlparse
import sys
import os
from datetime import datetime

def getCurrentDateTime():
    now = datetime.now()
    return now.strftime("%d_%m_%Y_%H_%M_%S")

def createWorkSessionFolder(createInPath):
    createdFolder = createInPath + "\\" + "session_" + getCurrentDateTime()
    os.mkdir(createdFolder)
    return createdFolder

workFolder = "C:\Data\GetLinks"
workSessionFolder = createWorkSessionFolder(workFolder)

def httpget(url):
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
    #links = []

    for a in soup.find_all('a'):
        url = a.get('href')
        links.add(url)
        #links.append(url)

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
    #allLinks = []
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
            #allLinks.extend(links)
            #print("allLinks.extend(links): {0}".format(endTime - startTime))
            print("allLinks.union(links): {0}".format(endTime - startTime))
            endTime = time.time()

    startTime = time.time()
    allLinksAsSet = allLinks
    #allLinksAsSet = set(allLinks)
    print("list to set: {0}".format(endTime - startTime))
    endTime = time.time()

    saveToFile(workSessionFolder, allLinksAsSet)

def validateArgs(args):
    if (args[1] is None or args[2] is None):
        print("Wrong arguments. 1st argument is the file of links, 2nd argument is the incremental value of how many pages to view.")
        return False

def main(args):
    #if (validateArgs(args) == False):
        #return

    #linksFilePath = str(args[1])
    #pagesCount = int(args[2])
    linksFilePath = "links2.txt"
    #linksFilePath = "links.txt"
    pagesCount = 10

    file = open(linksFilePath, "r")
    fileLines = file.readlines()
    file.close()

    incrementalUrls = []
    regularUrls = []

    for line in fileLines:
        if (isIncrementalUrl(line)):
            incrementalUrls.append(line)
        else:
            regularUrls.append(line)

    getLinksFromIncrementalUrls(incrementalUrls, pagesCount)
    #getLinks(regularUrls)

    cdi.quit()

if __name__ == '__main__':
    main(sys.argv)