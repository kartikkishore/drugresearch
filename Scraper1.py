from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import string
import time

DEBUG = False


def atc():
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

                    # Logging
                    print('Third Level: ', len(thirdCodes), thirdCodes, '\n') if DEBUG == True else None
                    for counter3 in thirdCodes:
                        driver.get('https://www.whocc.no/atc_ddd_index/' + '?code=' + counter3)

                        # Fourth level Scraping
                        text4 = []
                        if driver.page_source.__contains__('<td>Adm.R</td>'):
                            text4 = driver.find_element_by_xpath('//*[@id="content"]/ul/table/tbody').text.split('\n')

                            # Removing unnecessary rows
                            del text4[0]
                            text4 = [item.strip() for item in text4]

                            # Logging
                            print('Fourth level: ', len(text4), text4) if DEBUG == True else None

                            # Storing data
                            ATCinfo.append(text4)
                        else:
                            pass
        except(Exception):
            print('Error in ', letter, ', No data found')
    driver.close()
    return ATCinfo


def fda():
    FDAinfo = []
    chromeOptions = Options()
    chromeOptions.add_experimental_option("detach", True)
    driver = webdriver.Chrome(executable_path='./webdrivers/chromedriver', options=chromeOptions)
    for letter in string.ascii_uppercase:
        level = []
        driver.get('https://www.accessdata.fda.gov/scripts/cder/daf')
        driver.find_element_by_link_text(letter).click()
        numPages = driver.find_element_by_class_name('pagination').text.split('\n')[2:-2]
        for page in numPages:
            driver.find_element_by_link_text(page).click()
            level.append(driver.find_element_by_css_selector(
                '#mp-pusher > div > div > div > div > div.row.content > div > table > tbody').text.split('\n'))
        level = [item for sublist in level for item in sublist]
        level[0] = 'AUGMENTIN \'875\''
        # The list Level now contains every drug name with letter 'A'
        for drug in level:
            # Search for specific drug from level list
            driver.get('https://www.accessdata.fda.gov/scripts/cder/daf')
            search = driver.find_element_by_id('searchterm')
            search.send_keys(drug)
            driver.find_element_by_css_selector('#DrugNameform > div:nth-child(2) > button:nth-child(1)').click()
            time.sleep(1)

            # View results
            if 'Marketing' in driver.page_source:
                FDAinfo.append(driver.find_element_by_xpath('//*[@id="exampleProd"]/tbody').text)
            else:
                driver.find_element_by_link_text(drug).click()
                time.sleep(2)
                subcategories = len(driver.find_element_by_id('drugName1').text.split('\n'))
                for subDrugsCounter in range(1, subcategories + 1):
                    driver.get('https://www.accessdata.fda.gov/scripts/cder/daf')
                    search = driver.find_element_by_id('searchterm')
                    search.send_keys(drug)
                    driver.find_element_by_css_selector(
                        '#DrugNameform > div:nth-child(2) > button:nth-child(1)').click()
                    driver.find_element_by_link_text(drug).click()
                    time.sleep(2)
                    driver.find_element_by_xpath('//*[@id="drugName1"]/li[' + str(subDrugsCounter) + ']/a').click()
                    FDAinfo.append(driver.find_element_by_xpath('//*[@id="exampleProd"]/tbody').text)


if __name__ == '__main__':
    # print(atc())
    # print('ATC Success')
    fda()
