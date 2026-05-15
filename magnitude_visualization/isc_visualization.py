import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import geopandas as gpd
import numpy as np

# ── 1. Cargar datos ──────────────────────────────────────────────────────────
isc_csv = r"C:\Users\Beto\Desktop\Informatica\Investigación científica\scientific-research\data_files\ISC_data\ISC_output.csv"

df = pd.read_csv(isc_csv)
df['mb'] = pd.to_numeric(df['mb'], errors='coerce')
df_mapa = df[['lat', 'lon', 'mb']].dropna().copy()
df_mapa['lon'] = df_mapa['lon'] * -1

gdf_sismos = gpd.GeoDataFrame(
    df_mapa,
    geometry=gpd.points_from_xy(df_mapa.lon, df_mapa.lat),
    crs="EPSG:4326"
)

# ── 2. Mapa base ─────────────────────────────────────────────────────────────
url_estados = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
estados_eeuu = gpd.read_file(url_estados)
california = estados_eeuu[estados_eeuu['name'] == 'California']

# ── 3. Separar sismos por magnitud ───────────────────────────────────────────
gdf_pequenos = gdf_sismos[gdf_sismos['mb'] < 7]
gdf_grandes  = gdf_sismos[gdf_sismos['mb'] >= 7]

# ── 4. Figura ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 13))
fig.patch.set_facecolor('#0d1b2a')        # fondo exterior oscuro
ax.set_facecolor('#162032')               # fondo del mapa

# Contorno de California con relleno sutil
california.plot(ax=ax, color='#1e3048', edgecolor='#4a7fa5', linewidth=1.2)

# ── 5. Sismos pequeños: puntos coloreados por magnitud ───────────────────────
# Definir colores por rango de magnitud
rangos = [
    (gdf_pequenos['mb'] < 4,  '#5bc8f5', 18,  '< 4.0'),
    ((gdf_pequenos['mb'] >= 4) & (gdf_pequenos['mb'] < 5), '#f5c842', 30, '4.0 – 4.9'),
    ((gdf_pequenos['mb'] >= 5) & (gdf_pequenos['mb'] < 6), '#f59b42', 55, '5.0 – 5.9'),
    ((gdf_pequenos['mb'] >= 6) & (gdf_pequenos['mb'] < 7), '#e84545', 90, '6.0 – 6.9'),
]

for mask, color, size, _ in rangos:
    subset = gdf_pequenos[mask]
    if not subset.empty:
        subset.plot(ax=ax, marker='o', color=color, markersize=size**0.5 * 1.8,
                    alpha=0.7, linewidth=0.2, edgecolors='white')

# ── 6. Sismos grandes ≥ 7: estrellas ─────────────────────────────────────────
if not gdf_grandes.empty:
    ax.scatter(
        gdf_grandes.geometry.x, gdf_grandes.geometry.y,
        marker='*', s=350, color='#ff4466',
        edgecolors='white', linewidth=0.6,   # ← era linewidths
        zorder=10, alpha=0.95
    )

# ── 7. Ciudades (solo las más representativas para no saturar) ───────────────
ciudades_principales = {
    'Los Ángeles':    (34.0522, -118.2437),
    'San Francisco':  (37.7749, -122.4194),
    'San Diego':      (32.7157, -117.1611),
    'Sacramento':     (38.5816, -121.4944),
    'Fresno':         (36.7378, -119.7871),
    'San José':       (37.3382, -121.8863),
    'Bakersfield':    (35.3733, -119.0187),
    'Long Beach':     (33.7701, -118.1937),
    'Riverside':      (33.9806, -117.3755),
    'Stockton':       (37.9577, -121.2908),
    'Oakland':        (37.8044, -122.2712),
    'Santa Bárbara':  (34.4208, -119.6982),
    'Salinas':        (36.6777, -121.6555),
    'Redding':        (40.5865, -122.3917),
    'Palm Springs':   (33.8303, -116.5453),
    'Eureka':         (40.8021, -124.1637),
    'Ventura':        (34.2746, -119.2290),
    'Modesto':        (37.6391, -120.9969),
    'San Luis Obispo':(35.2828, -120.6596),
    'Chico':          (39.7285, -121.8375),
}

for ciudad, (lat, lon) in ciudades_principales.items():
    # Cuadrado blanco pequeño
    ax.plot(lon, lat, marker='s', color='white',
            markersize=4, zorder=8, linewidth=0)
    # Texto con borde negro para legibilidad
    txt = ax.text(lon + 0.12, lat + 0.05, ciudad,
                  fontsize=7.5, color='white', fontweight='bold',
                  zorder=9, ha='left', va='bottom')
    txt.set_path_effects([
        pe.withStroke(linewidth=2, foreground='#0d1b2a')
    ])

# ── 8. Leyenda ────────────────────────────────────────────────────────────────
colores_legend = ['#5bc8f5', '#f5c842', '#f59b42', '#e84545']
etiquetas = ['< 4.0', '4.0 – 4.9', '5.0 – 5.9', '6.0 – 6.9']
handles = [
    mpatches.Patch(color=c, label=f'mb {e}')
    for c, e in zip(colores_legend, etiquetas)
]
# Estrella para ≥ 7
from matplotlib.lines import Line2D
handles.append(Line2D([0], [0], marker='*', color='w',
                       markerfacecolor='#ff4466', markersize=12,
                       label='mb ≥ 7.0', linestyle='None'))
handles.append(Line2D([0], [0], marker='s', color='w',
                       markerfacecolor='white', markersize=5,
                       label='Ciudad', linestyle='None'))

legend = ax.legend(
    handles=handles,
    title='Magnitud (mb)',
    title_fontsize=9,
    fontsize=8,
    loc='upper right',
    facecolor='#0d1b2a',
    edgecolor='#4a7fa5',
    labelcolor='white',
    framealpha=0.9
)
legend.get_title().set_color('white')

# ── 9. Detalles finales ───────────────────────────────────────────────────────
ax.set_title('Actividad Sísmica en California',
             fontsize=16, fontweight='bold',
             color='white', pad=14)

ax.set_xlabel('Longitud', color='#8ab4cc', fontsize=9)
ax.set_ylabel('Latitud',  color='#8ab4cc', fontsize=9)
ax.tick_params(colors='#8ab4cc', labelsize=8)
for spine in ax.spines.values():
    spine.set_edgecolor('#4a7fa5')

ax.grid(True, linestyle='--', alpha=0.15, color='white')
ax.set_xlim(-125, -114)
ax.set_ylim(32, 42.5)

plt.tight_layout()
plt.savefig('california_sismos.png', dpi=150, bbox_inches='tight',
            facecolor=fig.get_facecolor())
plt.show()