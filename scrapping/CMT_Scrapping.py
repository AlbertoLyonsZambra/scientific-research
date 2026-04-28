import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import os

def get_info(
    start_date={"yr": "2023", "mo": "1", "day": "1"},
    end_date={"oyr": "2023", "omo": "12", "oday": "31"},
    latitudes={"llat": "32", "ulat": "42"},
    longitudes={"llon": "-124", "ulon": "-114"},
    link="https://www.globalcmt.org/CMTsearch.html"
):
    options = webdriver.EdgeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--log-level=3')

    driver = webdriver.Edge(options=options)
    
    print(f"Abriendo Global CMT: {link}")
    driver.get(link)
    wait = WebDriverWait(driver, 60)

    # Establecer la fecha en modo año-mes-día
    date_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='otype'][value='ymd']")))
    date_button.click()

    # Combinar todos los parámetros
    form_data = {**start_date, **end_date, **latitudes, **longitudes}

    print("Rellenando formulario...")
    for field_name, value in form_data.items():
        try:
            field = wait.until(EC.presence_of_element_located((By.NAME, field_name)))
            field.clear()
            field.send_keys(str(value))
        except Exception as e:
            print(f"No se pudo rellenar el campo {field_name}: {e}")

    # Enviar formulario
    submit_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='submit'][value='Done']")))
    submit_button.click()

    # Esperar resultados
    time.sleep(5)
    page_source = driver.page_source
    driver.quit()

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

    if not df.empty:
        # Crear directorios si no existen
        os.makedirs("CMT_data/excelFiles", exist_ok=True)

        # Construir nombre del archivo base
        y1, m1, d1 = start_date.get("yr", "????"), str(start_date.get("mo", "??")).zfill(2), str(start_date.get("day", "??")).zfill(2)
        y2, m2, d2 = end_date.get("oyr", "????"), str(end_date.get("omo", "??")).zfill(2), str(end_date.get("oday", "??")).zfill(2)
        blat = str(latitudes.get("llat", "?")).replace("-", "S").replace(".", "p")
        tlat = str(latitudes.get("ulat", "?")).replace("-", "S").replace(".", "p")
        llon = str(longitudes.get("llon", "?")).replace("-", "W").replace(".", "p")
        rlon = str(longitudes.get("ulon", "?")).replace("-", "W").replace(".", "p")
        
        stem = f"{y1}{m1}{d1}-{y2}{m2}{d2}_lat{blat}to{tlat}_lon{llon}to{rlon}"
        xlsx_path = os.path.join("CMT_data/excelFiles", stem + ".xlsx")
        
        # Convert columns to appropriate types before saving
        df["date"] = pd.to_datetime(df["date"])
        
        df.to_excel(xlsx_path, index=False, sheet_name="CMT_Earthquakes")
        print(f"[*] Excel de CMT guardado en: {xlsx_path}")

    return df

if __name__ == "__main__":
    # Test block
    df = get_info(
        start_date={"yr": "2023", "mo": "02", "day": "06"},
        end_date={"oyr": "2023", "omo": "02", "oday": "07"}
    )
    print("Datos extraídos exitosamente:")
    print(df)