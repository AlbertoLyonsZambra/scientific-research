from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup
import os
from pathlib import Path
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service

options = webdriver.EdgeOptions()

#options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--log-level=3')
options.add_argument('--enable-chrome-browser-cloud-management')

driver = webdriver.Edge(options=options)

def get_info(link):
    driver.get(link)
    wait = WebDriverWait(driver, 60)

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    """date range"""

    starting_year_field = wait.until(
            EC.presence_of_element_located((By.NAME, "yr"))
        )
    starting_month_field = wait.until(
            EC.presence_of_element_located((By.NAME, "mo"))
        )
    starting_day_field = wait.until(
            EC.presence_of_element_located((By.NAME, "day"))
        )
    ending_year_field = wait.until(
            EC.presence_of_element_located((By.NAME, "oyr"))
        )
    ending_month_field = wait.until(
            EC.presence_of_element_located((By.NAME, "omo"))
        )
    ending_day_field = wait.until(
            EC.presence_of_element_located((By.NAME, "oday"))
        )
    """
    Latitude and longitude range
    """
    starting_latitude_field = wait.until(
            EC.presence_of_element_located((By.NAME, "llat"))
        )
    ending_latitude_field = wait.until(
            EC.presence_of_element_located((By.NAME, "ulat"))
        )
    starting_longitude_field = wait.until(
            EC.presence_of_element_located((By.NAME, "llon"))
        )
    ending_longitude_field = wait.until(
            EC.presence_of_element_located((By.NAME, "ulon"))
        )
    """
    Submit (Done button)
    """
    submit_button = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='submit'][value='Done']"))
        )

    starting_year_field.clear()
    starting_month_field.clear()
    starting_day_field.clear()
    ending_year_field.clear()
    ending_month_field.clear()
    ending_day_field.clear()

    starting_latitude_field.clear()
    ending_latitude_field.clear()
    starting_longitude_field.clear()
    ending_longitude_field.clear()

    year_ending_date_button = driver.find_element(By.CSS_SELECTOR, "input[name='otype'][value='ymd']")
    year_ending_date_button.click()
    
    starting_year = input("Ingrese el año de inicio (numérico): ")
    starting_month = input("Ingrese el mes de inicio (numérico): ")
    starting_day = input("Ingrese el día de inicio (numérico): ")
    ending_year = input("Ingrese el año de fin (numérico): ")
    ending_month = input("Ingrese el mes de fin (numérico): ")
    ending_day = input("Ingrese el día de fin (numérico): ")

    starting_year_field.send_keys(starting_year)
    starting_month_field.send_keys(starting_month)
    starting_day_field.send_keys(starting_day)
    ending_year_field.send_keys(ending_year)
    ending_month_field.send_keys(ending_month)
    ending_day_field.send_keys(ending_day)

    starting_latitude = input("Ingrese una latitud de inicio (Entre -90 y 90): ")
    ending_latitude = input("Ingrese una latitud de fin (Entre -90 y 90): ")
    starting_longitude = input("Ingrese una longitud de inicio (Entre -180 y 180): ")
    ending_longitude = input("Ingrese una longitud de fin (Entre -180 y 180): ")

    starting_latitude_field.send_keys(starting_latitude)
    ending_latitude_field.send_keys(ending_latitude)
    starting_longitude_field.send_keys(starting_longitude)
    ending_longitude_field.send_keys(ending_longitude)

    submit_button.click()
    time.sleep(10) # Debug Only

    """
    Next page after submit the info
    """
    wait = WebDriverWait(driver, 60)
    """
    articles = soup.find('article', 'card card--featured')
    for article in articles:
        img = article.find('img')
        return img
    """
    
def main(link="https://www.globalcmt.org/CMTsearch.html"):
    result = get_info(link)
    print(result)
main()