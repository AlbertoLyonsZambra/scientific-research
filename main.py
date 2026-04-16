import os
import warnings
# Suprimir warnings si los hay de las conexiones
warnings.filterwarnings('ignore')

from database import engine, Base
from models import Earthquake
from scrapping.CMT_Scrapping import get_info
import pandas as pd
from dotenv import load_dotenv

def initialize_database():
    print("Inicializando base de datos...")
    Base.metadata.create_all(bind=engine)

def fetch_and_store_data(year, start_month, start_day, end_month, end_day):
    print(f"[{year}] Ejecutando consulta de terremotos...")
    df = get_info(
        start_date={"yr": str(year), "mo": str(start_month), "day": str(start_day)},
        end_date={"oyr": str(year), "omo": str(end_month), "oday": str(end_day)},
        latitudes={"llat": "-90", "ulat": "90"},
        longitudes={"llon": "-180", "ulon": "180"}
    )
    
    if df.empty:
        print("No se encontraron registros.")
        return

    print("Datos extraídos:")
    print(df.head())

    print("\nGuardando en la base de datos...")
    try:
        # Pandas cuenta con una función excelente para enviar el dataframe directo a la tabla de SQLAlchemy
        df.to_sql("earthquakes", con=engine, if_exists="append", index=False)
        print(f"Exito: Se guardaron {len(df)} registros mapeados en la base de datos.")
    except Exception as e:
        # Si el error es de clave duplicada (event_id unique constraint), avisamos
        if "UNIQUE constraint failed" in str(e) or "Duplicate entry" in str(e):
            print("Algunos registros ya existían en la base de datos (Ignorando duplicados).")
        else:
            print(f"Hubo un error al guardar en la BD: {e}")

if __name__ == "__main__":
    # Cargar variables de entorno
    load_dotenv()
    CMT_SCRAPING_URL = os.getenv("CMT_SCRAPING_URL", "https://www.globalcmt.org/CMTsearch.html")
    ISC_SCRAPING_URL = os.getenv("ISC_SCRAPING_URL", "") # TODO implementar link y scrapping
    # 1. Crear las tablas SQLite/MySQL si no existen
    initialize_database()

    # 2. Preguntar al usuario las fechas y la zona que desea investigar
    print("\n--- BÚSQUEDA DE SISMOS (GLOBAL CMT) ---")
    start_year = input("Ingresa el AÑO de inicio (ej. 2023): ").strip()
    ending_year = input("Ingresa el AÑO de fin (ej. 2024): ").strip()
    
    start_month = input("Mes de inicio (ej. 2): ").strip()
    start_day = input("Día de inicio (ej. 6): ").strip()
    
    end_month = input("Mes de fin (ej. 2): ").strip()
    end_day = input("Día de fin (ej. 7): ").strip()

    print("\n--- FILTRO DE ZONA (Opcional - Presiona Enter para Todo el Mundo) ---")
    min_lat = input("Latitud Sur Mínima (ej. -90): ").strip() or "-90"
    max_lat = input("Latitud Norte Máxima (ej. 90): ").strip() or "90"
    min_lon = input("Longitud Oeste Mínima (ej. -180): ").strip() or "-180"
    max_lon = input("Longitud Este Máxima (ej. 180): ").strip() or "180"
    
    print("-" * 39)

    # 3. Extraer y guardar
    # En lugar de usar valores estáticos como antes, le pasamos tus nuevos parámetros
    print(f"[{start_year}] Ejecutando consulta de terremotos...")
    df = get_info(
        start_date={"yr": str(start_year), "mo": str(start_month), "day": str(start_day)},
        end_date={"oyr": str(ending_year), "omo": str(end_month), "oday": str(end_day)},
        latitudes={"llat": str(min_lat), "ulat": str(max_lat)},
        longitudes={"llon": str(min_lon), "ulon": str(max_lon)},
        link=CMT_SCRAPING_URL
    )
    
    if df.empty:
        print("No se encontraron registros.")
    else:
        print("Datos extraídos:")
        print(df.head())
    
        print("\nGuardando en la base de datos...")
        try:
            # Pandas cuenta con una función excelente para enviar el dataframe directo a la tabla de SQLAlchemy
            df.to_sql("earthquakes", con=engine, if_exists="append", index=False)
            print(f"Exito: Se guardaron {len(df)} registros mapeados en la base de datos.")
        except Exception as e:
            # Si el error es de clave duplicada (event_id unique constraint), avisamos
            if "UNIQUE constraint failed" in str(e) or "Duplicate entry" in str(e) or "duplicate key" in str(e):
                print("Algunos registros sugeridos ya existían en la base de datos (Ignorando duplicados).")
            else:
                print(f"Hubo un error al guardar en la BD: {e}")