import selenium.common.exceptions
from selenium import webdriver
import pandas as pd
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

import string


def atc():
    level1dict = {}
    # Configure chrome in detach mode to persist chrome window
    chromeOptions = Options()
    chromeOptions.add_experimental_option("detach", True)
    driver = webdriver.Chrome(executable_path='./webdrivers/chromedriver', options=chromeOptions)

    # Get ATC website
    driver.get('https://www.whocc.no/atc_ddd_index/')

    # Scraping begins
    searchBox = driver.find_element_by_xpath('//*[@id="content"]/form/table/tbody/tr/td[1]/input')

    # Insert loop for searching with all alphabets here
    alphabet = 'A'
    searchBox.send_keys(alphabet)
    driver.find_element_by_class_name('button').click()
    text = driver.find_element_by_id('content').text.split('\n')
    del text[0:2]
    del text[-1]
    firstCodes = [item[0:3] for item in text]
    driver.get('https://www.whocc.no/atc_ddd_index/' + '?code=' + firstCodes[8])

    #######
    text2 = driver.find_element_by_id('content').text.split('\n')
    del text2[0:2]
    del text2[-1]
    del text2[0]
    secondCodes = [item.split(' ')[0] for item in text2]
    print(secondCodes)
    driver.get('https://www.whocc.no/atc_ddd_index/' + '?code=' + secondCodes[0])
    # print(driver.find_element_by_id('content').text)


if __name__ == '__main__':
    atc()
    # print('Success')
