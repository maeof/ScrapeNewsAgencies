import abc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

import multiprocessing
from joblib import Parallel, delayed
from tqdm import tqdm

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

#chrome_options = Options()
#chrome_options.add_argument("--headless")

#service = Service('c:\\data\\chromedriver\\chromedriver.exe')
#service.start()
#cdi = webdriver.Chrome("c:\\data\\chromedriver\\chromedriver.exe", options=chrome_options)
#cdi = webdriver.Remote(service.service_url)

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import urllib3 as urllib
from urllib.parse import urlparse
import sys
import os
from datetime import datetime, date, timedelta

def main():
    url = "https://bitebuild-27293b5fe84cd6a2aaos.cloudax.dynamics.com/"
    chrome_options = Options()
    cdi = webdriver.Chrome("c:\\data\\chromedriver\\chromedriver.exe", options=chrome_options)
    # cdi.get(url)
    # time.sleep(5)
    # cdi.find_element_by_name("loginfmt").send_keys("mbagdonas@alnaax.onmicrosoft.com")
    # cdi.find_element_by_id("idSIButton9").click()
    # time.sleep(3)
    # cdi.refresh()
    # time.sleep(2)
    # cdi.find_element_by_name("passwd").sendKeys("rem")
    # cdi.find_element_by_id("idSIButton9").click()
    # time.sleep(3)
    # cdi.find_element_by_id("idSIButton9").click()
    # time.sleep(15)

    EMAILFIELD = (By.ID, "i0116")
    PASSWORDFIELD = (By.ID, "i0118")
    NEXTBUTTON = (By.ID, "idSIButton9")
    nobutton = (By.ID, "idBtn_Back")

    SETTINGSBUTTON = (By.CLASS_NAME, "button flyoutButton-Button dynamicsButton")
    MODULESLIST = (By.ID, "navPaneModuleID")
    cdi.get(url)

    # wait for email field and enter email
    WebDriverWait(cdi, 10).until(EC.element_to_be_clickable(EMAILFIELD)).send_keys("mbagdonas@alnaax.onmicrosoft.com")

    # Click Next
    WebDriverWait(cdi, 10).until(EC.element_to_be_clickable(NEXTBUTTON)).click()

    # wait for password field and enter password
    WebDriverWait(cdi, 10).until(EC.element_to_be_clickable(PASSWORDFIELD)).send_keys("rem")

    # Click Login - same id?
    WebDriverWait(cdi, 10).until(EC.element_to_be_clickable(NEXTBUTTON)).click()

    WebDriverWait(cdi, 10).until(EC.element_to_be_clickable(nobutton)).click()
    time.sleep(5)

    WebDriverWait(cdi, 10).until(EC.element_to_be_clickable(MODULESLIST)).click()

    for module in cdi.find_elements(By.CLASS_NAME, "modulesPane-module"):
        module.click()
        for links in cdi.find_elements(By.CLASS_NAME, "modulesFlyout-link    "):
            links.click()
            time.sleep(10)



    time.sleep(7)



    cdi.quit()

if __name__ == '__main__':
    main()