import os
from datetime import datetime

from requests import get
from requests.exceptions import RequestException
from contextlib import closing


def getCurrentDateTime():
    now = datetime.now()
    return now.strftime("%d_%m_%Y_%H_%M_%S")


def createWorkSessionFolder(createInPath):
    createdFolder = createInPath + "\\" + "session_" + getCurrentDateTime()
    os.mkdir(createdFolder)
    return createdFolder


def saveToFile(path, links):
    fileNameWithPath = path + "\\" + "result.csv" #TODO: result.csv is hardcoded, make it dynamic
    file = open(fileNameWithPath, "a+")
    for link in links:
        if (link is not None):
            file.write(link + "\n")
    file.close()


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
        log_error('Error during requests to {0} : {1}'.format(url, str(e))) #TODO: would this even work?
        return None


def isResponseOK(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()

    if resp.status_code != 200:
        saveToFile("C:\Data\GetLinks", [resp.status_code, resp.url]) #TODO: make it dynamic

    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)