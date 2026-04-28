import os
import warnings
import argparse

import sqlalchemy
# Suprimir warnings si los hay de las conexiones
warnings.filterwarnings('ignore')

from data.database import engine, Base
from data.models import Earthquake
from scrapping import CMT_Scrapping
import pandas as pd
from scrapping import ISC_Scrapping
from dotenv import load_dotenv

def initialize_database():
    print("Inicializando base de datos...")
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script para extraer datos de terremotos y guardarlos en una base de datos.")
    parser.add_argument("--page", help="Página para realizar la consulta (valores: cmt, isc)", default="cmt", choices=["cmt", "isc"])
    args = parser.parse_args()
    # Cargar variables de entorno
    load_dotenv()
    CMT_SCRAPING_URL = os.getenv("CMT_SCRAPING_URL", "https://www.globalcmt.org/CMTsearch.html")
    ISC_SCRAPING_URL = os.getenv("ISC_SCRAPING_URL", "http://www.isc.ac.uk/cgi-bin/web-db-run?request=REVIEWED&out_format=ISF&prime_only=on&include_phases=on&include_headers=on")
    # 1. Crear las tablas SQLite/MySQL si no existen
    initialize_database()

    # 2. Preguntar al usuario las fechas y la zona que desea investigar
    print("\n--- BÚSQUEDA DE SISMOS ---")
    print(f"\n--- PÁGINA {args.page.upper()} ---")
    start_year = input("Ingresa el AÑO de inicio (ej. 2023): ").strip()
    ending_year = input("Ingresa el AÑO de fin (ej. 2024): ").strip()
    
    start_month = input("Mes de inicio (ej. 2): ").strip()
    start_day = input("Día de inicio (ej. 6): ").strip()
    
    end_month = input("Mes de fin (ej. 2): ").strip()
    end_day = input("Día de fin (ej. 7): ").strip()
    start_time, end_time = "", ""
    if args.page.lower() == "isc":
        print("\n--- FILTRO DE HORA EN FORMATO 24H (Opcional - Presiona Enter para 00:00:00 y 23:59:59) ---")
        start_hour = input("Hora de inicio (ej. 0): ").strip() or "00"
        start_minute = input("Minuto de inicio (ej. 0): ").strip() or "00"
        start_second = input("Segundo de inicio (ej. 0): ").strip() or "00"
        end_hour = input("Hora de fin (ej. 23): ").strip() or "23"
        end_minute = input("Minuto de fin (ej. 59): ").strip() or "59"
        end_second = input("Segundo de fin (ej. 59): ").strip() or "59"
        start_time = f"{start_hour.zfill(2)}:{start_minute.zfill(2)}:{start_second.zfill(2)}"
        end_time = f"{end_hour.zfill(2)}:{end_minute.zfill(2)}:{end_second.zfill(2)}"
    # Opcion en caso de que se seleccione ISC

    print("\n--- FILTRO DE ZONA (Opcional - Presiona Enter para California) ---")
    min_lat = input("Latitud Sur Mínima (ej. 32): ").strip() or "32"
    max_lat = input("Latitud Norte Máxima (ej. 42): ").strip() or "42"
    min_lon = input("Longitud Oeste Mínima (ej. -124): ").strip() or "-124"
    max_lon = input("Longitud Este Máxima (ej. -114): ").strip() or "-114"

    print("-" * 39)

    # 3. Extraer y guardar
    # En lugar de usar valores estáticos como antes, le pasamos tus nuevos parámetros
    print(f"[{start_year}] Ejecutando consulta de terremotos...")
    df = pd.DataFrame()
    if args.page.lower() == "cmt":
        df = CMT_Scrapping.get_info(
            start_date={"yr": str(start_year), "mo": str(start_month), "day": str(start_day)},
            end_date={"oyr": str(ending_year), "omo": str(end_month), "oday": str(end_day)},
            latitudes={"llat": str(min_lat), "ulat": str(max_lat)},
            longitudes={"llon": str(min_lon), "ulon": str(max_lon)},
            link=CMT_SCRAPING_URL
        )
    elif args.page.lower() == "isc":
        df = ISC_Scrapping.get_info(
            start_date={"start_year": str(start_year), "start_month": str(start_month), "start_day": str(start_day), "start_time": start_time},
            end_date={"end_year": str(ending_year), "end_month": str(end_month), "end_day": str(end_day), "end_time": end_time},
            latitudes={"bot_lat": str(min_lat), "top_lat": str(max_lat)},
            longitudes={"left_lon": str(min_lon), "right_lon": str(max_lon)},
            link=ISC_SCRAPING_URL
        )
    if df.empty:
        print("No se encontraron registros.")
    else:
        print("Datos extraídos:")
        print(df.head())
    
        print("\nGuardando en la base de datos...")
        try:
            if args.page.lower() == "cmt":
                df.to_sql("cmt_earthquakes", con=engine, if_exists="append", index=False)
                print(f"Exito: Se guardaron {len(df)} registros en la base de datos.")

            elif args.page.lower() == "isc":
                # Consultar event_ids ya existentes (la tabla puede no existir aún)
                try:
                    with engine.connect() as conn:
                        result = conn.execute(
                            sqlalchemy.text("SELECT event_id FROM isc_earthquakes")
                        )
                        existing_ids = {row[0] for row in result}
                except Exception:
                    existing_ids = set()  # tabla vacía o todavía no creada

                df_new = df[~df["event_id"].isin(existing_ids)]

                if df_new.empty:
                    print("Todos los eventos ya existen en la base de datos. No se insertó nada.")
                else:
                    df_new.to_sql("isc_earthquakes", con=engine, if_exists="append", index=False)
                    print(f"Exito: Se guardaron {len(df_new)} registros nuevos "
                          f"({len(df) - len(df_new)} duplicados ignorados).")
        except Exception as e:
            # Si el error es de clave duplicada (event_id unique constraint), avisamos
            if "UNIQUE constraint failed" in str(e) or "Duplicate entry" in str(e) or "duplicate key" in str(e):
                print("Algunos registros sugeridos ya existían en la base de datos (Ignorando duplicados).")
            else:
                print(f"Hubo un error al guardar en la BD: {e}")