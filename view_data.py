import pandas as pd
from database import engine

def show_data():
    try:
        # Cargar todo lo de la tabla 'earthquakes' usando Pandas
        df = pd.read_sql_table("earthquakes", con=engine)
        
        if df.empty:
            print("La base de datos está vacía, ¡intenta ejecutar main.py primero!")
        else:
            print(f"La base de datos tiene {len(df)} registros:")
            print("-" * 50)
            print(df.to_string())
    except Exception as e:
        print(f"Error leyendo la base de datos: {e}")

if __name__ == "__main__":
    show_data()
