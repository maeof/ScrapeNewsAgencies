from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time

service = Service('c:\\data\\chromedriver\\chromedriver.exe')
service.start()
cdi = webdriver.Remote(service.service_url)
cdi.get('http://www.google.com/');
time.sleep(5) # Let the user actually see something!
cdi.quit()