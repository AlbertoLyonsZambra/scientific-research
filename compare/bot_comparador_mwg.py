import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def run_comparison_bot():
    csv_path = "data_files/Final_data/CaliforniaData.csv"
    print(f"[*] Cargando datos desde {csv_path}...")
    
    # Leer el CSV (asumiendo separador ';')
    df = pd.read_csv(csv_path, sep=";")
    
    # Asegurarnos de que las columnas existan
    required_cols = ['ms', 'mb', 'mw', 'mwg']
    for col in required_cols:
        if col not in df.columns:
            print(f"[!] Error: No se encontró la columna {col}")
            return
            
    print(f"[*] Datos cargados correctamente. Total de registros: {len(df)}")
    print("-" * 40)
    
    magnitudes = ['ms', 'mb', 'mw']
    reference = 'mwg'
    
    # Estadísticas
    for mag in magnitudes:
        # Calcular diferencia
        diff = df[mag] - df[reference]
        mae = diff.abs().mean()
        rmse = np.sqrt((diff**2).mean())
        mean_bias = diff.mean()
        
        print(f"Comparación: {mag.upper()} vs {reference.upper()}")
        print(f"  -> Sesgo medio (Bias): {mean_bias:.4f}")
        print(f"  -> Error Absoluto Medio (MAE): {mae:.4f}")
        print(f"  -> Raíz del Error Cuadrático Medio (RMSE): {rmse:.4f}")
        print("-" * 40)

    # Gráficos
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('Comparación de Magnitudes frente a MWG', fontsize=16)
    
    for i, mag in enumerate(magnitudes):
        ax = axes[i]
        ax.scatter(df[reference], df[mag], alpha=0.6, edgecolors='w', color='teal')
        
        # Línea 1:1
        min_val = min(df[reference].min(), df[mag].min())
        max_val = max(df[reference].max(), df[mag].max())
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', label='Línea 1:1 (Ideal)')
        
        ax.set_title(f'{mag.upper()} vs {reference.upper()}')
        ax.set_xlabel(f'Referencia ({reference.upper()})')
        ax.set_ylabel(f'Magnitud ({mag.upper()})')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()

    plt.tight_layout()
    output_img = 'compare/comparacion_magnitudes_mwg.png'
    plt.savefig(output_img, dpi=300)
    print(f"[*] Gráfico comparativo guardado en: {output_img}")

if __name__ == "__main__":
    run_comparison_bot()
