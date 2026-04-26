import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from datetime import datetime

def get_info(
    start_date={"start_year": "2023", "start_month": "1", "start_day": "1", "start_time": "00:00:00"},
    end_date={"end_year": "2023", "end_month": "12", "end_day": "31", "end_time": "23:59:59"},
    latitudes={"bot_lat": "32", "top_lat": "42"},
    longitudes={"left_lon": "-124", "right_lon": "-114"},
    link="https://www.isc.ac.uk/iscbulletin/search/catalogue/"
):
    options = webdriver.EdgeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--log-level=3')

    driver = webdriver.Edge(options=options)
    
    print(f"Abriendo Global ISC: {link}")
    driver.get(link)
    wait = WebDriverWait(driver, 60)

    # Combinar todos los parámetros
    form_data = {**start_date, **end_date, **latitudes, **longitudes}
    xml_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='out_format'][value='CATQuakeML']")))
    xml_button.click()
    print("Rellenando formulario...")
    for field_name, value in form_data.items():
        try:
            if (field_name in ["start_month", "start_day", "end_month", "end_day"]):
                field = wait.until(EC.presence_of_element_located((By.NAME, field_name)))
                select_field = Select(field)
                if field_name in ["start_month", "end_month"]:
                    select_field.select_by_value(str(value))
                else:
                    select_field.select_by_index(7)
                continue
            field = wait.until(EC.presence_of_element_located((By.NAME, field_name)))
            field.clear()
            field.send_keys(str(value))
        except Exception as e:
            print(f"No se pudo rellenar el campo {field_name}: {e}")

    # Enviar formulario
    submit_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='submit'][value='Output event catalogue']")))
    submit_button.click()

    time.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])

    # Esperar resultados
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "pretty-print")))
    page_source = driver.page_source
    driver.quit()

    print("Analizando HTML de resultados...")
    soup = BeautifulSoup(page_source, 'xml')
    # Extraer eventos
    events = []
    data = soup.find_all('event')
    for event in data:
        # PublicID
        id = event.get("publicID").split('=')[1]
        print("Terremoto con id: ", id)
        # Date
        origin = event.origin
        date = origin.time.value.text
        # Lat
        lat = origin.latitude.value.text    
        # Lon
        lon = origin.longitude.value.text
        # Depth
        depth = origin.depth.value.text
        # Catch all magnitudes
        magnitudes = event.find_all('magnitude')
        mw_mag = ""
        ms_mag = ""
        for magnitude in magnitudes:
            if mw_mag != "" and ms_mag != "":
                break
            if magnitude.type.text.lower() == "ms" and ms_mag == "":
                ms_mag = magnitude.mag.value.text
            elif magnitude.type.text.lower() == "mw" and mw_mag == "":
                mw_mag = magnitude.mag.value.text
        event = {
            "id": id,
            "date": date,
            "latitude": lat,
            "longitude": lon,
            "depth": depth,
            "ms_mag": ms_mag,
            "mw_mag": mw_mag
        }
        events.append(event)
        print("Evento resultante: ", event)
    # Final
    df = pd.DataFrame(events)
    return df

if __name__ == "__main__":
    # Test block
    df = get_info(
        start_date={"start_year": "2024", "start_month": "3", "start_day": "1", "start_time": "00:00:00"},
        end_date={"end_year": "2024", "end_month": "4", "end_day": "1", "end_time": "00:00:00"},
        latitudes={"bot_lat": "-90", "top_lat": "-50"},
        longitudes={"left_lon": "-180", "right_lon": "-100"}
    )
    print("Datos extraídos exitosamente:")
    print(df)