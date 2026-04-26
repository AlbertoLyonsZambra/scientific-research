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
    #options.add_argument('--headless')
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

    # Esperar resultados
    time.sleep(20)
    page_source = driver.page_source
    driver.quit()
    """
    print("Analizando HTML de resultados...")
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Extraer eventos
    events = []
    
    # Encontramos los bloques <hr>. Luego buscamos los <b> (EventID) y <pre> (Datos)
    b_tags = soup.find_all('b')
    pre_tags = soup.find_all('pre')
    
    # El primer <pre> a veces es el search criteria, así que podemos ignorarlo si no contiene "Date:"
    data_pres = [p for p in pre_tags if "Centroid Time:" in p.get_text()]
    
    # Los tags <b> al principio tienen el Event ID
    # Filtrar solo los <b> que se ven como "202302060128A "
    event_ids = []
    locations = []
    for b in b_tags:
        text = b.get_text().strip()
        if re.match(r'^\d{11,14}[A-Z\s]*$', text):
            event_ids.append(text)
            # Find location by looking right after the </b> tag
            loc_text = b.next_sibling
            if isinstance(loc_text, str):
                locations.append(loc_text.strip())
            else:
                locations.append("UNKNOWN")

    # Hacer el match entre identificadores y bloques pre (deben tener la misma longitud si la página es normal)
    min_len = min(len(event_ids), len(data_pres))
    
    for i in range(min_len):
        event_id = event_ids[i].strip()
        loc = locations[i].strip()
        pre_text = data_pres[i].get_text()
        
        # Parsed fields
        # Date: 2023/ 2/ 6   Centroid Time:  1:28:22.2 GMT
        date_match = re.search(r'Date:\s+(\d{4}/\s*\d+/\s*\d+)', pre_text)
        time_match = re.search(r'Centroid Time:\s+([\d\:\.\s]+)\s+GMT', pre_text)
        lat_match = re.search(r'Lat=\s*([-\d\.]+)', pre_text)
        lon_match = re.search(r'Lon=\s*([-\d\.]+)', pre_text)
        depth_match = re.search(r'Depth=\s*([-\d\.]+)', pre_text)
        mw_match = re.search(r'Mw\s*=\s*([-\d\.]+)', pre_text)
        mb_match = re.search(r'mb\s*=\s*([-\d\.]+)', pre_text)
        ms_match = re.search(r'Ms\s*=\s*([-\d\.]+)', pre_text)
        
        # Format the date nicely to YYYY-MM-DD
        date_str = None
        if date_match:
            raw_date = date_match.group(1).replace(" ", "")
            try:
                date_str = datetime.strptime(raw_date, "%Y/%m/%d").date().strftime("%Y-%m-%d")
            except:
                pass
                
        time_str = None
        if time_match:
            raw_time = time_match.group(1).replace(" ", "")
            if "." in raw_time:
                raw_time = raw_time.split(".")[0]
            try:
                time_str = ":".join(p.zfill(2) for p in raw_time.split(":"))
            except Exception:
                time_str = raw_time

        event = {
            "event_id": event_id,
            "location": loc,
            "date": date_str,
            "centroid_time": time_str,
            "latitude": float(lat_match.group(1)) if lat_match else None,
            "longitude": float(lon_match.group(1)) if lon_match else None,
            "depth": float(depth_match.group(1)) if depth_match else None,
            "mw": float(mw_match.group(1)) if mw_match else None,
            "mb": float(mb_match.group(1)) if mb_match else None,
            "ms": float(ms_match.group(1)) if ms_match else None
        }
        events.append(event)

    df = pd.DataFrame(events)
    """
    return df

if __name__ == "__main__":
    # Test block
    df = get_info(
        start_date={"start_year": "2023", "start_month": "2", "start_day": "6", "start_time": "00:00:00"},
        end_date={"end_year": "2023", "end_month": "2", "end_day": "7", "end_time": "23:59:59"},
        latitudes={"bot_lat": "32", "top_lat": "42"},
        longitudes={"left_lon": "-124", "right_lon": "-114"}
    )
    print("Datos extraídos exitosamente:")
    print(df)