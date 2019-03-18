import datetime
import json
import pickle
import string
import os
import time
from timeit import default_timer as timer

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

DEBUG = False
FDAMOCKTEST = True
DRUGMOCKTEST = True


def atc():
    ATCrefDict = {}
    ATCinfo = []
    # Configure chrome in detach mode to persist chrome window
    chromeOptions = Options()
    chromeOptions.add_experimental_option("detach", True)
    driver = webdriver.Chrome(executable_path='./webdrivers/chromedriver', options=chromeOptions)

    # Insert loop for searching with all alphabets here
    for letter in string.ascii_uppercase:
        alphabet = letter
        driver.get('https://www.whocc.no/atc_ddd_index/')
        searchBox = driver.find_element_by_xpath('//*[@id="content"]/form/table/tbody/tr/td[1]/input')
        searchBox.send_keys(alphabet)
        driver.find_element_by_class_name('button').click()
        try:
            # First level Scraping
            text = driver.find_element_by_id('content').text.split('\n')

            # Removing unnecessary rows
            del text[0:2]
            del text[-1]
            firstCodes = [item[0:3] for item in text]

            # Updating Level 1 code & meaning in dictionary: ATCrefDict
            ATCrefDict = {**ATCrefDict, **{item[0:3]: item[4:].strip() for item in text}}
            print('1st= ', ATCrefDict, '\n')
            # Logging
            print('First Level: ', len(firstCodes), firstCodes, '\n') if DEBUG == True else None
            for counter1 in firstCodes:
                driver.get('https://www.whocc.no/atc_ddd_index/' + '?code=' + counter1)

                # Second level Scraping
                text2 = driver.find_element_by_id('content').text.split('\n')

                # Removing unnecessary rows
                del text2[0:2]
                del text2[-1]
                del text2[0]
                secondCodes = [item.split(' ')[0] for item in text2]

                # Updating Level 2 code & meaning in dictionary: ATCrefDict
                ATCrefDict = {**ATCrefDict, **{item.split(' ')[0]: item[item.index(' ') + 1:] for item in text2}}
                print('2nd= ', ATCrefDict, '\n')
                # Logging
                print('Second Level: ', len(secondCodes), secondCodes, '\n') if DEBUG == True else None
                for counter2 in secondCodes:
                    driver.get('https://www.whocc.no/atc_ddd_index/' + '?code=' + counter2)

                    # Third level Scraping
                    text3 = driver.find_element_by_id('content').text.split('\n')

                    # Removing unnecessary rows
                    del text3[0:3]
                    del text3[-1]
                    del text3[0]
                    thirdCodes = [item.split(' ')[0] for item in text3]

                    # Updating Level 3 code & meaning in dictionary: ATCrefDict
                    ATCrefDict = {**ATCrefDict, **{item.split(' ')[0]: item[item.index(' ') + 1:] for item in text3}}

                    # Logging
                    print('Third Level: ', len(thirdCodes), thirdCodes, '\n') if DEBUG == True else None
                    for counter3 in thirdCodes:
                        driver.get('https://www.whocc.no/atc_ddd_index/' + '?code=' + counter3)

                        # Issue01 | Flag setting
                        Issue01 = False

                        # Fourth level Scraping
                        text4 = []
                        if driver.page_source.__contains__('<td>Adm.R</td>'):
                            tableBody = driver.find_element_by_xpath('//*[@id="content"]/ul/table/tbody')
                            rowOfDetails = tableBody.find_elements_by_tag_name('tr')
                            c1 = c2 = iv1 = iv2 = 0
                            # Issue01 | Special case: subcategory has no code or name - Inheriting the previous level
                            if rowOfDetails[0].text.split('  ')[0] == 'ATC code' and \
                                    len(rowOfDetails[1].text.split('  ')[0]) != 7:
                                iv1 = counter3 + '**'
                                iv2 = ATCrefDict[counter3].strip()
                                Issue01 = True
                            # Normal case - every detail present in the table
                            for element in rowOfDetails:
                                tempRow = [item.strip() for item in element.text.split('  ')]
                                print(len(tempRow), tempRow) if DEBUG == True else None
                                # Swapping & shifting logic
                                if len(tempRow) >= 5:
                                    c1, c2 = tempRow[0:2]
                                if len(tempRow) == 3:
                                    a, b, c = tempRow[0:3]
                                    tempRow = [c1, c2, a, b, c]
                                    if Issue01:
                                        tempRow = [iv1, iv2, a, b, c]
                                if len(tempRow) == 4:
                                    a, b, c, d = tempRow[0:4]
                                    tempRow = [c1, c2, a, b, c, d]
                                    if Issue01:
                                        tempRow = [iv1, iv2, a, b, c, d]
                                text4.append(tempRow) if 'ATC c' not in element.text else None
                                # Logging - New data added
                                print(tempRow) if DEBUG == True else None
                            # Storing data
                            ATCinfo.append(text4)
                        else:
                            pass
        except(Exception):
            print('Error in ', letter, ', No data found') if DEBUG == True else None
            pass
    driver.close()
    # Congregating
    ATCinfo = [item for sublist in ATCinfo for item in sublist]
    return [ATCinfo, ATCrefDict]


def fda():
    FDAinfo = FDAlinkList = []
    try:
        if FDAMOCKTEST:
            os.remove('data/fda/FDA_logger.csv')
    except Exception:
        None
    if FDAMOCKTEST is False:
        chromeOptions = Options()
        chromeOptions.add_experimental_option("detach", True)
        driver = webdriver.Chrome(executable_path='./webdrivers/chromedriver', options=chromeOptions)

        with tqdm(total=len(string.ascii_uppercase)) as alphabetScrapingProgress:
            for letter in string.ascii_uppercase:
                driver.get('https://www.accessdata.fda.gov/scripts/cder/daf')
                driver.find_element_by_link_text(letter).click()

                # Finding: All links for a particular letter are available in the table tag as per HTML structure
                # Page segmentation for the table is on a UI-UX level
                largeTable = driver.find_element_by_css_selector(
                    '#mp-pusher > div > div > div > div > div.row.content > div > table > tbody')

                # Scraping all links for that letter
                bulkLinks = [rowElement.get_attribute('href') for rowElement in
                             largeTable.find_elements_by_tag_name('a')]

                # Add to link set, discarding redirection and useless links
                [FDAlinkList.append(link) if 'browse' not in link else None for link in bulkLinks]
                alphabetScrapingProgress.update(1)
        driver.close()

    # For the purpose of mock-testing
    if FDAMOCKTEST:
        FDAlinkList = pickle.load(open('data/fda/FDAlink_pickle', 'rb'))

    # Saving set as pickle
    with open('data/fda/FDAlink_Pickle', 'wb') as fp:
        pickle.dump(FDAlinkList, fp)
    FDAFile = open('data/fda/FDA_logger.csv', 'a')

    sleepCounter = 0
    linkCompletedSet = set()
    errorPath = ''

    # Visit all scraped links one by one
    with tqdm(total=len(FDAlinkList)) as linkScrapper:
        for link in FDAlinkList:
            errorPath = 'data/fda/LinksCompleted_' + str(datetime.datetime.now().strftime('%m-%d-%H-%M'))
            sleepCounter += 1
            start, end = [0, 5]
            try:
                webPage = requests.get(link, timeout=100).text
                soup = BeautifulSoup(webPage)
                if 'Active Ingredients' in str(soup):
                    tableWithID_exampleProd = soup.find('table')
                    drugData = [item.text for item in tableWithID_exampleProd.find_all('td')]

                    # Slicing the data for the first 5 columns that we need
                    [FDAinfo.append(drugData[start + i:end + i]) if drugData[start + i:end + i] != [] else None for i in
                     range(0, 1000, 8)]

                    # Writing to file
                    [FDAFile.write(str(str(drugData[start + i:end + i]) + '\n')) if drugData[
                                                                                    start + i:end + i] != [] else None
                     for i in range(0, 1000, 8)]
                    FDAFile.flush()
                linkCompletedSet.add(link)
                linkScrapper.update(1)
                # Sleeping measures so as to not spam the website with requests
                if sleepCounter % 200 == 0:
                    time.sleep(15)
                if sleepCounter % 500 == 0:
                    time.sleep(30)
            except requests.exceptions.SSLError:
                time.sleep(100)
                with open(errorPath, 'wb') as fp:
                    pickle.dump(linkCompletedSet, fp)
                pass
            except requests.exceptions.Timeout:
                time.sleep(100)
                with open(errorPath, 'wb') as fp:
                    pickle.dump(linkCompletedSet, fp)
                pass
            except requests.exceptions.ConnectionError:
                time.sleep(100)
                with open(errorPath, 'wb') as fp:
                    pickle.dump(linkCompletedSet, fp)
                pass
    FDAFile.close()
    return FDAinfo


def drugs():
    drugsInfo = drugIndexLinks = drugView = []
    os.remove('data/drugs/drugs_logger.csv')

    chromeOptions = Options()
    chromeOptions.add_experimental_option("detach", True)
    driver = webdriver.Chrome(executable_path='./webdrivers/chromedriver', options=chromeOptions)

    if DRUGMOCKTEST is False:
        # Loop to find all drug names as per indexed pages
        for letter in string.ascii_lowercase:
            driver.get('https://www.drugs.com/alpha/' + letter + '.html')
            # Trying to find active html references for redirection
            topList = driver.find_element_by_class_name('ddc-paging')
            links = [item.get_attribute('href') for item in topList.find_elements_by_tag_name('a')]
            print(links) if DEBUG == True else None
            drugIndexLinks.append(links)

        # List: drugIndexLinks has all the available alphabets combinations, access them directly and extract data
        drugIndexLinks = [item for sublist in drugIndexLinks for item in sublist]

        with tqdm(total=len(drugIndexLinks)) as pbar:
            for link in drugIndexLinks:
                driver.get(link)
                drugTable = driver.find_element_by_css_selector('#content > div.contentBox > ul')
                eachDrugLink = [item.get_attribute('href') for item in drugTable.find_elements_by_tag_name('a')]
                print(eachDrugLink) if DEBUG == True else None
                drugView.append(eachDrugLink)
                time.sleep(2)
                pbar.update(1)

        # Now the list: drugView has all the drug page links
        drugView = [item for sublist in drugView for item in sublist]

        # Saving data to File
        with open('data/drugs/drugsLink_Pickle', 'wb') as fp:
            pickle.dump(drugView, fp)
    driver.close()

    if DRUGMOCKTEST:
        drugView = pickle.load(open('data/drugs/drugsLink_Pickle', 'rb'))
    del drugView[0:390]

    drugView = set(drugView)
    drugsFile = open('data/drugs/drugs_logger.csv', 'a')
    sleepCounter = 0

    with tqdm(total=len(drugView)) as drugsDotComBar:
        for link in drugView:
            sleepCounter += 1

            drugsDotComBar.update(1)
            # Ignoring natural products
            if 'https://www.drugs.com/npc' in str(link):
                pass
            else:
                webPage = requests.get(link, timeout=100).text
                soup = BeautifulSoup(webPage)
                try:
                    x = soup.find('p', attrs={'class': 'drug-subtitle'}).text
                    drugsFile.write(str(x.split('\n')) + '|' + link + '\n')
                    drugsFile.flush()
                except AttributeError:
                    try:
                        brandNamesUS = soup.find('h2', string='Brand Names: U.S.')
                        bUS = brandNamesUS.find_next('ul').text.split('\n')
                        print('Brand US', bUS, link)
                        drugsFile.write(str(bUS) + '|' + link + '\n')
                        drugsFile.flush()
                    except AttributeError:
                        try:
                            inTheUS = soup.find('b', string='In the U.S.')
                            iUS = inTheUS.find_next('ul').text.split('\n')
                            print('In the US', iUS, link)
                            del iUS[0]
                            del iUS[-1]
                            drugsFile.write(str(iUS) + '|' + link + '\n')
                            drugsFile.flush()
                        except AttributeError:
                            try:
                                inCanada = soup.find('b', string='In Canada')
                                iC = inCanada.find_next('ul').text.split('\n')
                                print('In Canada', iC, link)
                                del iC[0]
                                del iC[-1]
                                drugsFile.write(str(iC) + '|' + link + '\n')
                                drugsFile.flush()
                            except AttributeError:
                                try:
                                    name = soup.find('div', attrs={'class': 'contentBox'}).find_next('h1').text
                                    text = soup.find('div', attrs={'class': 'contentBox'}).find_next('p').text
                                    drugsFile.write(name + '|' + text + '|' + link + '\n')
                                except Exception:
                                    print('Odd Link:', link)
    return drugsInfo


def chembl():
    chromeOptions = Options()
    chromeOptions.add_experimental_option("detach", True)
    driver = webdriver.Chrome(executable_path='./webdrivers/chromedriver', options=chromeOptions)
    wait = WebDriverWait(driver, 200)
    driver.get('https://www.ebi.ac.uk/chembl/')
    time.sleep(2)
    driver.find_element_by_id('keyword').clear()
    searchBox = driver.find_element_by_id('keyword')
    searchBox.send_keys('A-HYDROCORT')
    driver.find_element_by_css_selector('#compound_button > span > span > span:nth-child(1)').click()
    try:
        wait.until(expected_conditions.visibility_of_element_located((By.ID, 'bodyHeaderTitle')))
        if '0 Hits' in driver.find_element_by_id('bodyHeaderTitle').text:
            print('No result found for the compound:') if DEBUG == True else None
        else:
            time.sleep(2)
            table = driver.find_element_by_id('example')
            linksToChemical = [item.get_attribute('href') for item in table.find_elements_by_tag_name('a')]
            print(linksToChemical) if DEBUG == True else None
            for link in linksToChemical:
                driver.get(link)
                print(driver.find_element_by_class_name('contenttable_lmenu').text)
    except Exception:
        print('Page loading issue') if DEBUG == True else None


def findATC_Levels_123(fourthLevelCode, ATC_Level_Dict):
    newATCDict = {}
    for key, value in ATC_Level_Dict.items():
        newATCDict[key] = value.replace(',', ' &')
    print(newATCDict) if DEBUG == True else None
    tempLevelString = []
    for key, value in newATCDict.items():
        if fourthLevelCode.startswith(key):
            tempLevelString.append(key)
            tempLevelString.append(value)
    print(fourthLevelCode, len(tempLevelString), tempLevelString) if DEBUG == True else None
    return tempLevelString


def writeIntermediateryToFile(fileAsInput, dataframe):
    # This is just for debugging purposes
    with open('data/atc/ATC_Level_Dict.json', 'w') as file:
        file.write(json.dumps(fileAsInput))
    dataframe.to_csv('data/atc/ATC_Intermediatery_Data.csv', index=None)


if __name__ == '__main__':
    # #########################
    # # ATC Report Generation #
    # #########################
    # startTime = timer()
    # ATClevel4array, ATC_Level_Dict = atc()
    #
    # # Creating Dataframe for text processing
    # ATC_DataFrame = pd.DataFrame.from_records(ATClevel4array, columns=['ATC_Code', 'Name', 'DDD', 'U', 'Adm.R', 'Note'])
    #
    # # Intermediatery save dictionary - For validation purposes
    # writeIntermediateryToFile(ATC_Level_Dict) if DEBUG == True else None
    #
    # # Data processing
    # ATC_DataFrame['L1_Code'] = ATC_DataFrame['ATC_Code'].apply(lambda x: findATC_Levels_123(x, ATC_Level_Dict)[0])
    # ATC_DataFrame['L1_Name'] = ATC_DataFrame['ATC_Code'].apply(lambda x: findATC_Levels_123(x, ATC_Level_Dict)[1])
    # ATC_DataFrame['L2_Code'] = ATC_DataFrame['ATC_Code'].apply(lambda x: findATC_Levels_123(x, ATC_Level_Dict)[2])
    # ATC_DataFrame['L2_Name'] = ATC_DataFrame['ATC_Code'].apply(lambda x: findATC_Levels_123(x, ATC_Level_Dict)[3])
    # ATC_DataFrame['L3_Code'] = ATC_DataFrame['ATC_Code'].apply(lambda x: findATC_Levels_123(x, ATC_Level_Dict)[4])
    # ATC_DataFrame['L3_Name'] = ATC_DataFrame['ATC_Code'].apply(lambda x: findATC_Levels_123(x, ATC_Level_Dict)[5])
    # ATC_DataFrame = ATC_DataFrame[
    #     ['L1_Code', 'L1_Name', 'L2_Code', 'L2_Name', 'L3_Code', 'L3_Name', 'ATC_Code', 'Name', 'DDD', 'U', 'Adm.R',
    #      'Note']]
    # ATC_DataFrame.to_csv('data/atc/ATC Dump ' + str(datetime.datetime.now().strftime('%Y-%m-%d')) + '.csv', index=None)
    # print('ATC Dump generated in {} seconds'.format(timer() - startTime))
    #########################
    # FDA Report Generation #
    #########################
    # temp = fda()
    drugs()
