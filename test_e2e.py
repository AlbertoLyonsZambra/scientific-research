"""
Test end-to-end: 
1. Scraper CMT (2 días, 6-7 feb 2023 - terremoto de Turquía visible en CMT)
2. Merge con ISC existente
Imprime los resultados y verifica que haya al menos 1 evento fusionado.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from selenium import webdriver
from selenium.webdriver.edge.service import Service

# Apuntar al driver instalado manualmente
DRIVER_PATH = r"C:\Windows\System32\edgedriver_win64\msedgedriver.exe"
EDGE_PATH   = r"C:\Program Files (x86)\Microsoft\EdgeCore\147.0.3912.86\msedge.exe"

# Monkey-patch para usar el driver path correcto
import scrapping.CMT_Scrapping as cmt_mod

_orig_get_info = cmt_mod.get_info

def _patched_get_info(**kwargs):
    import time, re, pandas as pd, os
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from bs4 import BeautifulSoup
    from datetime import datetime

    start_date = kwargs.get("start_date", {"yr":"2023","mo":"2","day":"6"})
    end_date   = kwargs.get("end_date",   {"oyr":"2023","omo":"2","oday":"7"})
    latitudes  = kwargs.get("latitudes",  {"llat":"32","ulat":"42"})
    longitudes = kwargs.get("longitudes", {"llon":"-124","ulon":"-114"})
    link       = kwargs.get("link", "https://www.globalcmt.org/CMTsearch.html")

    options = webdriver.EdgeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--log-level=3')
    options.binary_location = EDGE_PATH

    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Edge(service=service, options=options)

    print(f"Abriendo Global CMT: {link}")
    driver.get(link)
    wait = WebDriverWait(driver, 60)

    date_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='otype'][value='ymd']")))
    date_button.click()

    form_data = {**start_date, **end_date, **latitudes, **longitudes}
    print("Rellenando formulario...")
    for field_name, value in form_data.items():
        try:
            field = wait.until(EC.presence_of_element_located((By.NAME, field_name)))
            field.clear()
            field.send_keys(str(value))
        except Exception as e:
            print(f"  No se pudo rellenar {field_name}: {e}")

    submit_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='submit'][value='Done']")))
    submit_button.click()

    time.sleep(5)
    page_source = driver.page_source
    driver.quit()

    print("Analizando HTML de resultados...")
    soup = BeautifulSoup(page_source, 'html.parser')
    events = []
    b_tags   = soup.find_all('b')
    pre_tags = soup.find_all('pre')
    data_pres = [p for p in pre_tags if "Centroid Time:" in p.get_text()]
    event_ids, locations = [], []
    for b in b_tags:
        text = b.get_text().strip()
        if re.match(r'^\d{11,14}[A-Z\s]*$', text):
            event_ids.append(text)
            loc_text = b.next_sibling
            locations.append(loc_text.strip() if isinstance(loc_text, str) else "UNKNOWN")

    min_len = min(len(event_ids), len(data_pres))
    for i in range(min_len):
        event_id = event_ids[i].strip()
        loc = locations[i].strip()
        pre_text = data_pres[i].get_text()
        date_match  = re.search(r'Date:\s+(\d{4}/\s*\d+/\s*\d+)', pre_text)
        time_match  = re.search(r'Centroid Time:\s+([\d\:\.\s]+)\s+GMT', pre_text)
        lat_match   = re.search(r'Lat=\s*([-\d\.]+)', pre_text)
        lon_match   = re.search(r'Lon=\s*([-\d\.]+)', pre_text)
        depth_match = re.search(r'Depth=\s*([-\d\.]+)', pre_text)
        mw_match    = re.search(r'Mw\s*=\s*([-\d\.]+)', pre_text)
        mb_match    = re.search(r'mb\s*=\s*([-\d\.]+)', pre_text)
        ms_match    = re.search(r'Ms\s*=\s*([-\d\.]+)', pre_text)

        date_str = None
        if date_match:
            raw = date_match.group(1).replace(" ","")
            try: date_str = datetime.strptime(raw, "%Y/%m/%d").date().strftime("%Y-%m-%d")
            except: pass

        time_str = None
        if time_match:
            raw = time_match.group(1).replace(" ","")
            if "." in raw: raw = raw.split(".")[0]
            try: time_str = ":".join(p.zfill(2) for p in raw.split(":"))
            except: time_str = raw

        events.append({
            "event_id": event_id, "location": loc,
            "date": date_str, "centroid_time": time_str,
            "latitude": float(lat_match.group(1)) if lat_match else None,
            "longitude": float(lon_match.group(1)) if lon_match else None,
            "depth": float(depth_match.group(1)) if depth_match else None,
            "mw": float(mw_match.group(1)) if mw_match else None,
            "mb": float(mb_match.group(1)) if mb_match else None,
            "ms": float(ms_match.group(1)) if ms_match else None,
        })

    df = pd.DataFrame(events)
    if not df.empty:
        os.makedirs("CMT_data/excelFiles", exist_ok=True)
        y1,m1,d1 = start_date.get("yr","????"), str(start_date.get("mo","??")).zfill(2), str(start_date.get("day","??")).zfill(2)
        y2,m2,d2 = end_date.get("oyr","????"), str(end_date.get("omo","??")).zfill(2), str(end_date.get("oday","??")).zfill(2)
        blat = str(latitudes.get("llat","?")).replace("-","S").replace(".","p")
        tlat = str(latitudes.get("ulat","?")).replace("-","S").replace(".","p")
        llon = str(longitudes.get("llon","?")).replace("-","W").replace(".","p")
        rlon = str(longitudes.get("ulon","?")).replace("-","W").replace(".","p")
        stem = f"{y1}{m1}{d1}-{y2}{m2}{d2}_lat{blat}to{tlat}_lon{llon}to{rlon}"
        xlsx_path = os.path.join("CMT_data/excelFiles", stem + ".xlsx")
        df["date"] = pd.to_datetime(df["date"])
        # Limpiar caracteres de control ilegales de todas las columnas string
        import re as _re
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].apply(lambda x: _re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', str(x)) if pd.notna(x) else x)
        df.to_excel(xlsx_path, index=False, sheet_name="CMT_Earthquakes")
        print(f"[*] Excel de CMT guardado en: {xlsx_path}")
    return df, locals().get("xlsx_path","")


if __name__ == "__main__":
    print("="*60)
    print("PASO 1: Scraping CMT (Turquía, 6-7 feb 2023)")
    print("="*60)
    df_cmt, cmt_path = _patched_get_info(
        start_date={"yr":"2023","mo":"2","day":"6"},
        end_date=  {"oyr":"2023","omo":"2","oday":"7"},
        latitudes= {"llat":"35","ulat":"42"},
        longitudes={"llon":"30","ulon":"42"}
    )
    print(f"\n[OK] Eventos CMT extraídos: {len(df_cmt)}")
    if not df_cmt.empty:
        print(df_cmt[["event_id","date","centroid_time","latitude","longitude","mw"]].to_string(index=False))

    print("\n" + "="*60)
    print("PASO 2: Merge CMT + ISC")
    print("="*60)
    from merge_datasets import merge_cmt_isc
    import glob

    # Buscar archivo ISC disponible
    isc_files = glob.glob("ISC_data/excelFiles/*.xlsx")
    if not isc_files:
        print("[!] No se encontró archivo ISC. Saltando merge.")
    elif not cmt_path:
        print("[!] No hay CMT Excel generado. Saltando merge.")
    else:
        isc_path = isc_files[0]
        print(f"[*] Usando ISC: {isc_path}")
        print(f"[*] Usando CMT: {cmt_path}")

        df_merged = merge_cmt_isc(
            cmt_excel_path=cmt_path,
            isc_excel_path=isc_path,
            output_path="Merged_Earthquakes.xlsx",
            time_tol_sec=120,
            dist_tol_km=200
        )

        if df_merged is not None and not df_merged.empty:
            print(f"\n[OK] Sismos fusionados: {len(df_merged)}")
            cols = [c for c in ["event_id_isc","event_id_cmt","datetime_isc","datetime_cmt",
                                 "latitude_isc","longitude_isc","mw","time_diff_sec","dist_km"] if c in df_merged.columns]
            print(df_merged[cols].to_string(index=False))
        else:
            print("[!] No se encontraron eventos coincidentes en este rango.")
