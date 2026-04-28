import pandas as pd
import numpy as np

def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia del círculo polar máximo entre dos puntos 
    en la tierra (especificados en grados decimales).
    Retorna la distancia en kilómetros.
    """
    # Convertir a radianes
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    
    # Fórmula de Haversine
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    r = 6371 # Radio de la tierra en km
    return c * r

def merge_cmt_isc(cmt_excel_path, isc_excel_path, output_path, time_tol_sec=120, dist_tol_km=200):
    """
    Fusiona los catálogos de CMT e ISC.
    :param cmt_excel_path: Ruta al archivo Excel de CMT
    :param isc_excel_path: Ruta al archivo Excel de ISC
    :param output_path: Ruta donde guardar el Excel combinado
    :param time_tol_sec: Tolerancia de tiempo en segundos para considerar que es el mismo sismo
    :param dist_tol_km: Tolerancia de distancia en kilómetros (2 grados son aprox 222 km)
    """
    try:
        print(f"[*] Cargando archivo CMT: {cmt_excel_path}")
        df_cmt = pd.read_excel(cmt_excel_path)
    except Exception as e:
        print(f"[!] Error al cargar CMT: {e}")
        return None
        
    try:
        print(f"[*] Cargando archivo ISC: {isc_excel_path}")
        df_isc = pd.read_excel(isc_excel_path)
    except Exception as e:
        print(f"[!] Error al cargar ISC: {e}")
        return None

    if df_cmt.empty or df_isc.empty:
        print("[!] Uno de los archivos está vacío. No se puede fusionar.")
        return pd.DataFrame()

    # Preparar df_cmt: Crear una columna datetime_cmt
    # La columna 'date' es datetime o string (YYYY-MM-DD), 'centroid_time' es string (HH:MM:SS)
    df_cmt['date_str'] = pd.to_datetime(df_cmt['date']).dt.strftime('%Y-%m-%d')
    # Algunas filas podrían no tener centroid_time válido, llenamos con 00:00:00
    df_cmt['centroid_time'] = df_cmt['centroid_time'].fillna('00:00:00').astype(str)
    
    df_cmt['datetime_cmt'] = pd.to_datetime(df_cmt['date_str'] + ' ' + df_cmt['centroid_time'], errors='coerce')
    
    # Preparar df_isc: 'date' ya es el origen con fecha y hora
    df_isc['datetime_isc'] = pd.to_datetime(df_isc['date'], errors='coerce')

    # Para hacer el cruce de manera eficiente, podemos hacer un 'cross join' de los sismos
    # que ocurrieron en la misma fecha (ignorando la hora para el join inicial, y luego filtrando)
    df_cmt['join_date'] = df_cmt['datetime_cmt'].dt.date
    df_isc['join_date'] = df_isc['datetime_isc'].dt.date

    print(f"[*] Sismos en CMT: {len(df_cmt)}")
    print(f"[*] Sismos en ISC: {len(df_isc)}")

    # Agregamos sufijos para diferenciar las columnas que se llamen igual
    merged = pd.merge(df_isc, df_cmt, on='join_date', suffixes=('_isc', '_cmt'), how='inner')
    
    if merged.empty:
        print("[!] No se encontraron sismos en la misma fecha.")
        return merged

    # Filtrar por diferencia de tiempo
    merged['time_diff_sec'] = (merged['datetime_isc'] - merged['datetime_cmt']).dt.total_seconds().abs()
    
    # Filtrar por diferencia de distancia (Haversine)
    # merged['latitude_isc'], merged['longitude_isc'] ...
    merged['dist_km'] = haversine(
        merged['latitude_isc'], merged['longitude_isc'],
        merged['latitude_cmt'], merged['longitude_cmt']
    )

    # Aplicar tolerancias
    final_df = merged[(merged['time_diff_sec'] <= time_tol_sec) & (merged['dist_km'] <= dist_tol_km)].copy()

    # Limpiar columnas temporales
    final_df.drop(columns=['join_date', 'date_str'], inplace=True, errors='ignore')

    # Ordenar por fecha del ISC
    final_df.sort_values(by='datetime_isc', inplace=True)
    final_df.reset_index(drop=True, inplace=True)

    print(f"[*] Sismos fusionados encontrados: {len(final_df)}")
    
    if not final_df.empty:
        final_df.to_excel(output_path, index=False, sheet_name="Merged_Earthquakes")
        print(f"[✓] Archivo fusionado guardado en: {output_path}")
    else:
        print("[!] No hubo sismos que cumplan con las tolerancias de tiempo y distancia.")

    return final_df

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fusionar datos de CMT e ISC")
    parser.add_argument("--cmt", required=True, help="Ruta al archivo Excel de CMT")
    parser.add_argument("--isc", required=True, help="Ruta al archivo Excel de ISC")
    parser.add_argument("--out", default="Merged_Earthquakes.xlsx", help="Ruta de salida")
    args = parser.parse_args()
    
    merge_cmt_isc(args.cmt, args.isc, args.out)
