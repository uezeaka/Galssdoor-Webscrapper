import re
import pandas as pd
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, NoSuchElementException
# NOTE: Install "xlrd" and "XlsxWriter" Libraries if you intend to save DatFrame as excel

# DataFrame display settings
pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 11)

def Glassdoor_Scrapper(position: str, location: str, amount: int, recent: bool = True, save_Dataframe: bool = False):
    """
    Selenium script for scrapping job information from Glassdoor.com (Specifically for Mozilla Firefox).

    :param position: The job position of interest - (String)
    :param location: The geographical area of interest (within 25mi radius) - (String)
    :param amount: The number of jobs you want - (Numerical object (int))
    :param recent: Option to sort jobs by the most recent (Default is True) - (Boolean)
    :param save_Dataframe: Option to save your dataframe (Default is False) - (Boolean)
    :return: DataFrame of job information queried by the provided parameters.
    """

    # Opens new Firefox browser and maximizes window
    driver = webdriver.Firefox()
    driver.maximize_window()

    # Uses webdriver get() to load website's url
    driver.get('https://www.glassdoor.com/Job/index.htm')

    sleep(5)
    # Explicitly wait for username and password elements to be interacted, then passes items within their respective fields
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'KeywordSearch'))).send_keys(position)
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'LocationSearch'))).clear()
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'LocationSearch'))).send_keys(location)

    sleep(1)
    # Explicitly wait 1 second then click "search" button
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'HeroSearchButton'))).click()

    sleep(5)
    # List to save collected job information
    full_job_data = []

    # "Company Overview" HTML elements, would be used for retrieving additional company information
    company_overview = ['Size', 'Founded', 'Type', 'Industry', 'Sector', 'Revenue']

    # Pandas DataFrame column names
    data_columns = ['Company', 'Position', 'Location', 'Rating', 'Salary Estimate', 'Size', 'Founded', 'Type', 'Industry', 'Sector', 'Revenue']

    # If recent is True, recent job postings are scrapped else, the most relevant job postings are scrapped
    if recent:
        driver.find_element_by_css_selector('[class="css-150lexj e1gtdke60"]').click()
        sleep(1)
        driver.find_element_by_css_selector('[data-test="date_desc"]').click()

    while (len(full_job_data) < amount):
        # Selects the first job posting to trigger "Sign-up" pop-up
        try:
            driver.find_element_by_class_name('selected').click()
        except ElementClickInterceptedException:
            pass

        sleep(2)

        # Closes "Sign-up" pop-up in the situation where it does appear
        try:
            driver.find_element_by_css_selector('[alt="Close"]').click()
        except NoSuchElementException:
            pass

        sleep(2)

        # Retrieves the number of jobs present on page
        page_length = len(driver.find_elements_by_class_name('jl')) + 1

        for index in range(1, page_length):
            # If collected data equals your requested job amount, exit loop
            if (len(full_job_data) == amount):
                break

            sleep(2)

            # Selecting each posting on job page for scrapping information
            driver.find_element_by_xpath('.//ul[@class ="jlGrid hover "]/li[{}]'.format(index)).click()

            # Iterative condition for exiting loop after collecting company's name, job role and location
            search_complete = False

            sleep(4)

            while not search_complete:
                # Retrieving company's name, job role, and location information
                try:
                    company_name = driver.find_element_by_xpath('.//div[@class ="empInfo newDetails"]/div[1]').text
                    company_role = driver.find_element_by_xpath('.//div[@class ="empInfo newDetails"]/div[2]').text
                    company_location = driver.find_element_by_xpath('.//div[@class ="empInfo newDetails"]/div[3]').text
                    search_complete = True

                # Capturing "stale elements" - the element no longer appears on the DOM (Document Object Model) of the page
                ## More information on stale elements: https://www.selenium.dev/exceptions/
                except StaleElementReferenceException:
                    sleep(4)

            sleep(1)

            # Retrieving Company rating ("nan" if not provided)
            try:
                driver.find_element_by_xpath('.//span[@class="rating"]')
                rating = company_name[-3:]

            except NoSuchElementException:
                rating = 'nan'

            sleep(1)

            # Retrieving company salary (NOTE: Information isn't always provided)
            try:
                # Using Regular Expression to separate and remove '(Glassdoor est.)' string slice from salary info
                salary = re.split('\s\(.*\)', driver.find_element_by_xpath('.//div[@class ="empInfo newDetails"]/div[4]').text)[0]

            except NoSuchElementException:
                salary = 'nan'

            # Appending all job information within a list
            ## Using Regular Expression (Regex) split() method to remove '\n[Company Rating]' from company's name
            job_info = [re.split('(\\n.*)', company_name)[0], company_role, company_location, rating, salary]

            sleep(1)

            # Iterating over 'Company' tab and retrieving company size, founding date, type, industry, sector and annual revenue
            try:
                driver.find_element_by_xpath('.//div[@data-tab-type="overview"]').click()
                company_info = []
                sleep(3)

                # For-Loop for iterating over company information using company_overview list elements (Line 49)
                for element in company_overview:
                    try:
                        company_info.append(driver.find_element_by_xpath('.//label[text()="{}"]/following-sibling::span'.format(element)).text)

                    # If specific company information doesn't exit, the value is passed as "nan"
                    except NoSuchElementException:
                        company_info.append('nan')

            # If "Company Overview" tab doesn't exist, all values are instead passed as "nan"
            except NoSuchElementException:
                company_info = ['nan', 'nan', 'nan', 'nan', 'nan', 'nan']

            # Concatenate both job_info and company_info lists containing full job information
            full_job_data.append(job_info + company_info)
            print("Progress Report: Collected {} out of {} jobs.".format((len(full_job_data)), amount))

        # All information has been collected within current job page.
        ## Condition only met, all data within current page has been collected but the script has not gathered the number of jobs you wanted
        if (len(full_job_data) < amount):
            sleep(2)
            # Select "next" button to move to next page
            driver.find_element_by_xpath('.//a[@data-test="pagination-next"]').click()

    # Creating DataFrame of all data that has been created, data_columns (Line 52) used as column names
    job_df = pd.DataFrame(full_job_data, columns=data_columns)

    # If save_Dataframe parameter is set to True, the created DataFrame is saved on your device as a spreadsheet
    ## NOTE: Ensure "xlrd" and "XlsxWriter" Libraries are installed
    if save_Dataframe:
        writer = pd.ExcelWriter('Glassdoor Jobs.xlsx', engine='xlsxwriter')
        job_df.to_excel(writer, index=False)
        writer.save()

    return job_df
