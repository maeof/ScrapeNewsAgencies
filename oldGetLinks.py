from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import urllib3 as urllib
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
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if isResponseOK(resp):
                return resp.content
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

def getIncrementalUrl(url, i):
    return url.replace("{0}", str(i))

def isIncrementalUrl(url):
    if (url.find("{0}") != -1):
        return True
    else:
        return False

def getLinksFromPageContent(pageContent):
    soup = BeautifulSoup(pageContent, 'html.parser')
    links = []

    for a in soup.find_all('a'):
        links.append(a.get('href'))

    return links

def saveToFile(path, links):
    fileNameWithPath = path + "\\" + "result.csv"
    file = open(fileNameWithPath, "w+")
    for link in links:
        if (link is not None):
            file.write(link + "\r\n")
    file.close()

def getLinks(regularUrls):
    for url in regularUrls:
        pageContent = httpget(url)
        links = getLinksFromPageContent(pageContent)
        saveToFile(workSessionFolder, links)

def getLinksFromIncrementalUrls(incrementalUrls, pagesCount):
    for i in range(1, pagesCount):
        for url in incrementalUrls:
            urlForRequest = getIncrementalUrl(url, i)
            pageContent = httpget(urlForRequest)
            links = getLinksFromPageContent(pageContent)
            saveToFile(workSessionFolder, links)

def validateArgs(args):
    if (args[1] is None or args[2] is None):
        print("Wrong arguments. 1st argument is the file of links, 2nd argument is the incremental value of how many pages to view.")
        return False

def main(args):
    if (validateArgs(args) == False):
        return

    linksFilePath = str(args[1])
    pagesCount = int(args[2])

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
    getLinks(regularUrls)

if __name__ == '__main__':
    main(sys.argv)