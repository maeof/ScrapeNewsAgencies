from urllib.parse import urlparse
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

def main():
    linksFile = "C:\\Data\\AnalyzeLinks\\links.csv"

    workFolder = "C:\Data\AnalyzeLinks"
    workSessionFolder = createWorkSessionFolder(workFolder)
    resultFile = workSessionFolder + "\\" + "result.csv"

    cpuCount = multiprocessing.cpu_count()

    inputFile = open(linksFile, "r")
    urls = inputFile.readlines()
    inputFile.close()

    processedList = Parallel(n_jobs=cpuCount)(delayed(processUrl)(url, workSessionFolder) for url in urls)

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