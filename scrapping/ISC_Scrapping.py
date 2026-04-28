import urllib.request as urllib
import os
import sys
import re
import datetime as dt

import numpy as np
import pandas as pd

# Permite visualizar el avance del proceso en la terminal
class _ProgressBar:
    def __init__(self, max_value, label="Processing"):
        self.max_value = max_value
        self.label = label

    def start(self):
        sys.stdout.write(f"[...] {self.label}\n")
        sys.stdout.flush()

    def update(self, curr_value):
        bar_width = 40
        progress  = curr_value / self.max_value if self.max_value else 1
        block     = int(bar_width * progress)
        bar       = "[" + "=" * block + " " * (bar_width - block) + "]"
        sys.stdout.write(f"\r  {bar} {curr_value}/{self.max_value}")
        sys.stdout.flush()

    def finish(self):
        sys.stdout.write("\n[✓] Done\n\n")
        sys.stdout.flush()

# Permite construir la URL de consulta y descargar el boletín ISC
class _Downloader:

    # El constructor recibe los parámetros de consulta y la URL base
    def __init__(self, params: dict, base_url: str):
        self.params = params
        self.base_url = base_url

    # Construye la URL de consulta
    def build_url(self) -> str:
        query = "&".join(f"{k}={v}" for k, v in self.params.items() if v is not None)
        return self.base_url + "&" + query

    # Descarga el boletín ISC y lo guarda en un archivo crudo
    def download(self, save_raw=True, raw_path="bulletin_raw.txt") -> str:
        url = self.build_url()
        print(f"[*] URL de consulta:\n    {url}\n")

        # Barra de progreso para la descarga
        def _reporthook(block_num, block_size, total_size):
            if total_size <= 0:
                # El ISC no siempre envía Content-Length, mostramos KB descargados
                downloaded_kb = (block_num * block_size) / 1024
                print(f"\r  Descargando... {downloaded_kb:.1f} KB", end="\r", flush=True)
            else:
                downloaded = min(block_num * block_size, total_size)
                progress   = downloaded / total_size
                bar_width  = 40
                block      = int(bar_width * progress)
                bar        = "=" * block + " " * (bar_width - block)
                mb_done    = downloaded / (1024 * 1024)
                mb_total   = total_size / (1024 * 1024)
                print(f"\r  [{bar}] {mb_done:.2f}/{mb_total:.2f} MB", end="\r", flush=True)

        try:
            print("[*] Descargando boletín ISC...")
            tmp_path, _ = urllib.urlretrieve(url, reporthook=_reporthook)
            print()    # salto de línea al terminar
            print("[✓] Descarga completa\n")
        except Exception as e:
            sys.exit(f"[ERROR] Fallo al descargar: {e}")

        with open(tmp_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        os.remove(tmp_path)

        if save_raw:
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[*] Boletín crudo guardado en: {raw_path}")

        # Extraer cuerpo del interior del HTML
        if "<html" in content.lower():
            match = re.search(r"<pre[^>]*>(.*?)</pre>", content, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                print("[*] Contenido extraído del HTML correctamente")
            else:
                # HTML sin <pre> → error real del servidor
                snippet = re.sub(r"<[^>]+>", " ", content)
                snippet = re.sub(r"\s+", " ", snippet).strip()[:400]
                raise ValueError(
                    f"El servidor devolvió HTML sin datos.\n"
                    f"Mensaje del servidor: {snippet}"
                )
        if "No events were found" in content:
            sys.exit("[!] No events were found. Amplía el rango de búsqueda.")

        return content

# Permite parsear el contenido del boletín ISC y extraer la información relevante de cada evento y fase
class _CATCSVParser:
    """
    Parsea el formato EVENT_CATALOGUE (CATCSV) del ISC.
 
    Cada línea de evento tiene la forma:
        EVENTID, TYPE, AUTHOR, DATE, TIME, LAT, LON, DEPTH, DEPFIX,
        [AUTHOR, TYPE, MAG, ...]   ← repetido N veces
    """
 
    # Índice donde empiezan los grupos de magnitud (tras el campo DEPFIX)
    _MAG_START_COL = 9
 
    @staticmethod
    def _strip_html(line: str) -> str:
        """Elimina cualquier tag HTML de una línea preservando el texto interior."""
        return re.sub(r"<[^>]+>", "", line)

    def parse(self, content: str) -> list[dict]:
        # Extraer sólo el bloque de datos entre la cabecera y STOP
        body = re.split(r"\s*STOP\s*", content, flags=re.IGNORECASE)[0]
 
        # Eliminar líneas de encabezado (DATA_TYPE, ----EVENT-----, etc.)
        data_lines = []
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            # Saltamos cabeceras y comentarios
            if line.startswith(("DATA_TYPE", "Reviewed", "----", "EVENTID",
                                 "#", "International", "ISC")):
                continue
            # Una línea de datos empieza con un número entero (EVENTID)
            if re.match(r"^\d+\s*,", line):
                data_lines.append(line)
 
        print(f"[*] Eventos encontrados: {len(data_lines)}")
        if not data_lines:
            sys.exit("[!] No se encontraron eventos en el boletín CATCSV.")
 
        pbar = _ProgressBar(len(data_lines), label="Parseando CATCSV...")
        pbar.start()
 
        events = []
        for i, line in enumerate(data_lines):
            ev = self._parse_line(line)
            if ev:
                events.append(ev)
            pbar.update(i + 1)
 
        pbar.finish()
        print(f"[*] Eventos parseados: {len(events)}")
        return events
 
    def _parse_line(self, line: str) -> dict | None:
        # Separar por comas; la línea puede terminar en coma
        cols = [c.strip() for c in line.rstrip(",").split(",")]
 
        if len(cols) < 9:
            return None
 
        event_id = cols[0]
        author   = cols[2]      # agencia del hipocentro
        date_str = cols[3]
        time_str = cols[4]
        lat_str  = cols[5]
        lon_str  = cols[6]
        dep_str  = cols[7]
        depfix   = cols[8].upper() == "TRUE"
 
        # Fecha/hora de origen
        try:
            origin_time = dt.datetime.strptime(
                f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S.%f"
            )
        except ValueError:
            try:
                origin_time = dt.datetime.strptime(
                    f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                return None
 
        try:
            lat   = float(lat_str)
            lon   = float(lon_str)
            depth = float(dep_str)
        except ValueError:
            return None
 
        # Magnitudes: a partir de la columna 9, grupos de 3 (AUTHOR, TYPE, VALUE)
        # Se expanden directamente como claves mag_<TYPE>_<AUTHOR>
        mag_cols = cols[self._MAG_START_COL:]
        magnitudes = {}
        for j in range(0, len(mag_cols) - 2, 3):
            mag_author = mag_cols[j].strip()
            mag_type   = mag_cols[j + 1].strip()
            mag_val    = mag_cols[j + 2].strip()
 
            if not mag_author or not mag_type or not mag_val:
                continue
            try:
                key = f"mag_{mag_type}_{mag_author}".lower()  # Normalizar a minúsculas para evitar colisiones
                val = float(mag_val)
                # Si ya existe, conservar el mayor (más representativo)
                if key in magnitudes:
                    magnitudes[key] = max(magnitudes[key], val)
                else:
                    magnitudes[key] = val
            except ValueError:
                continue
 
        return {
            "event_id":     event_id,
            "date":         origin_time.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "latitude":     lat,
            "longitude":    lon,
            "depth":        depth,
            "depth_fixed":  depfix,
            "hypo_author":  author,
            "n_magnitudes": len(magnitudes),
            **magnitudes,  # mag_<TYPE>_<AUTHOR> directamente en el dict del evento
        }
    
 
def _ensure_dirs():
    """Crea las carpetas de salida si no existen."""
    os.makedirs("ISC_data/txtFiles",  exist_ok=True)
    os.makedirs("ISC_data/excelFiles", exist_ok=True)


# Permite construir un nombre de archivo descriptivo para guardar el boletín crudo
def _build_file_stem(start_date: dict, end_date: dict,
                    latitudes: dict, longitudes: dict) -> str:
    
    y1 = start_date.get("start_year",  "????")
    m1 = str(start_date.get("start_month", "??")).zfill(2)
    d1 = str(start_date.get("start_day",   "??")).zfill(2)

    y2 = end_date.get("end_year",  "????")
    m2 = str(end_date.get("end_month", "??")).zfill(2)
    d2 = str(end_date.get("end_day",   "??")).zfill(2)

    blat = str(latitudes.get("bot_lat",  "?")).replace("-", "S").replace(".", "p")
    tlat = str(latitudes.get("top_lat",  "?")).replace("-", "S").replace(".", "p")
    llon = str(longitudes.get("left_lon",  "?")).replace("-", "W").replace(".", "p")
    rlon = str(longitudes.get("right_lon", "?")).replace("-", "W").replace(".", "p")

    return f"{y1}{m1}{d1}-{y2}{m2}{d2}_lat{blat}to{tlat}_lon{llon}to{rlon}"


# Permite descargar el boletín ISC y retorna un DataFrame
def get_info(
    start_date: dict  = None,   #{"start_year", "start_month", "start_day", "start_time"}
    end_date:   dict  = None,   #{"end_year", "end_month", "end_day", "end_time"}
    latitudes:  dict  = None,   #{"bot_lat", "top_lat"}
    longitudes: dict  = None,   #{"left_lon", "right_lon"}
    link:       str   = None,
    searchshape: str  = "RECT", #"RECT" | "GLOBAL" | "CIRC" | "POLY"
    min_mag:    float = None,
    max_mag:    float = None,
    min_dep:    float = None,
    max_dep:    float = None,
) -> pd.DataFrame:
    
    start_date  = start_date  or {}
    end_date    = end_date    or {}
    latitudes   = latitudes   or {}
    longitudes  = longitudes  or {}

    # Crear carpetas de salida si no existen
    _ensure_dirs()

    # Constriur el nombre del archivo crudo
    stem = _build_file_stem(start_date, end_date, latitudes, longitudes)

    raw_path  = os.path.join("ISC_data/txtFiles",  stem + ".txt")
    xlsx_path = os.path.join("ISC_data/excelFiles", stem + ".xlsx")

    # Construir el dict de parámetros para la API
    api_params = {
        "searchshape": searchshape,
        **latitudes,
        **longitudes,
        **start_date,
        **end_date,
    }
    if min_mag is not None:
        api_params["min_mag"] = min_mag
    if max_mag is not None:
        api_params["max_mag"] = max_mag
    if min_dep is not None:
        api_params["min_dep"] = min_dep
    if max_dep is not None:
        api_params["max_dep"] = max_dep

    # 1 · Descarga
    downloader = _Downloader(api_params, link)
    content    = downloader.download(save_raw=True, raw_path=raw_path)

    # 2 · Parseo
    parser = _CATCSVParser()
    events = parser.parse(content)

    if not events:
        print("[!] No se generó ningún evento válido.")
        return pd.DataFrame()

    # 3 · DataFrame y limpieza
    df = pd.DataFrame(events)
    df["date"]      = pd.to_datetime(df["date"])
    df["latitude"]  = pd.to_numeric(df["latitude"],  errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["depth"]     = pd.to_numeric(df["depth"],     errors="coerce")

    # Convertir columnas mag_* a numérico (vienen como float pero por seguridad)
    mag_cols = [c for c in df.columns if c.startswith("mag_")]
    for col in mag_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Filtrar eventos sin ninguna magnitud
    before = len(df)
    df = df[df["n_magnitudes"] > 0]
    print(f"[*] Eventos sin magnitud eliminados: {before - len(df)} "
        f"({len(df)} restantes)")

    # Eliminar duplicados por event_id (si los hay) y resetear índice
    df.drop_duplicates(subset="event_id", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # 4 · Exportar a Excel
    df.to_excel(xlsx_path, index=False, sheet_name="ISC_Earthquakes")
    print(f"[*] Excel guardado en: {xlsx_path}")

    # 5 · Retornar DataFrame
    print(f"[✓] DataFrame listo: {len(df)} eventos\n")
    return df

# Permite realizar una prueba rápida del proceso
if __name__ == "__main__":
    df = get_info(
        start_date={"start_year": "2020", "start_month": "1",
                    "start_day": "1",  "start_time": "00:00:00"},
        end_date={"end_year":   "2020", "end_month": "3",
                  "end_day":   "31",  "end_time": "23:59:59"},
        latitudes={"bot_lat": "32", "top_lat": "42"},
        longitudes={"left_lon": "-125", "right_lon": "-114"},
        min_mag=3.0,
    )
    print(df.head())
    print("\nColumnas:", df.columns.tolist())
    print(df.dtypes)