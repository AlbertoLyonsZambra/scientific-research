# Scientific Research - Global CMT & ISC Earthquake Pipeline

Sistema automatizado para extraer, limpiar y fusionar catálogos sísmicos de [Global CMT](https://www.globalcmt.org) e [ISC](https://www.isc.ac.uk). El pipeline descarga eventos sísmicos de ambas fuentes, los exporta a Excel limpio y los cruza espaciotemporalmente para generar un dataset consolidado.

---

## 📁 Estructura del Proyecto

```
scientific-research/
├── scrapping/
│   ├── CMT_Scrapping.py       # Scraper de Global CMT → guarda Excel en CMT_data/excelFiles/
│   └── ISC_Scrapping.py       # Scraper de ISC → guarda Excel en ISC_data/excelFiles/
├── CMT_data/
│   └── excelFiles/            # Excels limpios generados por CMT_Scrapping.py
├── ISC_data/
│   └── excelFiles/            # Excels limpios generados por ISC_Scrapping.py
├── merge_datasets.py          # Fusiona CMT + ISC por proximidad espaciotemporal
├── tests/
│   └── test_merge_datasets.py # Tests unitarios y de integración (pytest)
├── data/
│   ├── database.py
│   └── models.py
├── main.py
├── requirements.txt
└── .env.example
```

---

## ⚙️ Requisitos Previos

- **Python 3.8+**
- **Git**
- **Microsoft Edge** (para el scraper de CMT, que usa Selenium)
- **msedgedriver** con la misma versión que tu Edge instalado → [Descargar aquí](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)

---

## 🚀 Instalación (Windows PowerShell)

### 1. Clonar el repositorio
```powershell
git clone https://github.com/AlbertoLyonsZambra/scientific-research.git
cd scientific-research
```

### 2. Configurar Variables de Entorno
```powershell
cp .env.example .env
```
> Por defecto usa SQLite local, no necesita configuración extra.

### 3. Crear entorno virtual e instalar dependencias
```powershell
# (Solo una vez) Habilitar scripts en PowerShell:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🔄 Pipeline Completo: CMT + ISC → Dataset Fusionado

El pipeline tiene **3 pasos** en secuencia:

---

### Paso 1 — Extraer datos de CMT y exportar a Excel limpio

Ejecuta el scraper de CMT para un rango de fechas y región geográfica:

```python
# scrapping/CMT_Scrapping.py
from scrapping.CMT_Scrapping import get_info

df_cmt = get_info(
    start_date={"yr": "2023", "mo": "1",  "day": "1"},
    end_date=  {"oyr": "2023", "omo": "12", "oday": "31"},
    latitudes= {"llat": "32", "ulat": "42"},
    longitudes={"llon": "-124", "ulon": "-114"}
)
```

O directamente desde terminal:
```powershell
python scrapping/CMT_Scrapping.py
```

**Resultado:** Se genera automáticamente un archivo Excel en `CMT_data/excelFiles/` con nombre basado en fechas y coordenadas, por ejemplo:
```
CMT_data/excelFiles/20230101-20231231_lat32to42_lonW124toW114.xlsx
```

El Excel incluye las columnas: `event_id`, `location`, `date`, `centroid_time`, `latitude`, `longitude`, `depth`, `mw`, `mb`, `ms`.

---

### Paso 2 — Extraer datos de ISC y exportar a Excel limpio

El scraper de ISC funciona de manera análoga y guarda el resultado en `ISC_data/excelFiles/`. Este archivo **ya existe** en el repositorio si fue generado previamente.

---

### Paso 3 — Fusionar CMT + ISC

Una vez que tienes ambos Excels, ejecuta el script de fusión:

```powershell
python merge_datasets.py \
    --cmt "CMT_data/excelFiles/20230101-20231231_lat32to42_lonW124toW114.xlsx" \
    --isc "ISC_data/excelFiles/19700101-20240101_lat32to42_lonW124toW114.xlsx" \
    --out "Merged_Earthquakes.xlsx"
```

O bien, úsalo como módulo desde Python:

```python
from merge_datasets import merge_cmt_isc

df = merge_cmt_isc(
    cmt_excel_path="CMT_data/excelFiles/20230101-20231231_lat32to42_lonW124toW114.xlsx",
    isc_excel_path="ISC_data/excelFiles/19700101-20240101_lat32to42_lonW124toW114.xlsx",
    output_path="Merged_Earthquakes.xlsx",
    time_tol_sec=120,   # Tolerancia temporal: ±2 minutos
    dist_tol_km=200     # Tolerancia espacial: ±200 km
)
print(f"Sismos fusionados: {len(df)}")
```

**Criterios de fusión:**
| Criterio | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| Tolerancia tiempo | 120 segundos | Diferencia máxima entre `centroid_time` (CMT) y hora de origen (ISC) |
| Tolerancia distancia | 200 km | Distancia máxima calculada con la fórmula de **Haversine** |

**Resultado:** Archivo `Merged_Earthquakes.xlsx` con todos los campos de ambas fuentes, columnas diferenciadas con sufijos `_cmt` e `_isc`, ordenado cronológicamente.

---

## 🧪 Tests

El proyecto incluye **16 tests** que verifican la lógica del merge sin necesidad de datos reales ni conexión a internet:

```powershell
python -m pytest tests/test_merge_datasets.py -v
```

Salida esperada:
```
tests/test_merge_datasets.py::TestHaversine::test_same_point_is_zero        PASSED
tests/test_merge_datasets.py::TestHaversine::test_known_distance_equator    PASSED
tests/test_merge_datasets.py::TestHaversine::test_symmetry                  PASSED
tests/test_merge_datasets.py::TestHaversine::test_antipodal_points          PASSED
tests/test_merge_datasets.py::TestHaversine::test_returns_float             PASSED
tests/test_merge_datasets.py::TestMergeCmtIsc::test_returns_none_if_cmt_path_invalid  PASSED
tests/test_merge_datasets.py::TestMergeCmtIsc::test_returns_none_if_isc_path_invalid  PASSED
tests/test_merge_datasets.py::TestMergeCmtIsc::test_returns_empty_df_if_cmt_empty     PASSED
tests/test_merge_datasets.py::TestMergeCmtIsc::test_returns_empty_df_if_isc_empty     PASSED
tests/test_merge_datasets.py::TestMergeCmtIsc::test_match_correct_event               PASSED
tests/test_merge_datasets.py::TestMergeCmtIsc::test_no_match_when_time_tol_very_small PASSED
tests/test_merge_datasets.py::TestMergeCmtIsc::test_no_match_when_dist_tol_very_small PASSED
tests/test_merge_datasets.py::TestMergeCmtIsc::test_output_excel_is_created           PASSED
tests/test_merge_datasets.py::TestMergeCmtIsc::test_output_excel_readable             PASSED
tests/test_merge_datasets.py::TestMergeCmtIsc::test_result_sorted_by_isc_datetime     PASSED
tests/test_merge_datasets.py::TestMergeCmtIsc::test_temp_columns_removed              PASSED

========================= 16 passed in 0.77s =========================
```

---

## 🖥 Uso del Web Scrapper (flujo legacy)

Para usar el sistema interactivo completo con base de datos SQLite:
```powershell
python main.py
```

Para verificar los datos insertados:
```powershell
python view_data.py
```

## ⚙️ Requisitos Previos

Necesitarás tener instalados:
- **Python 3.8+**
- **Git** 

---

## 🚀 Instalación y Despliegue Rápido (Windows PowerShell)

Sigue estos pasos en tu terminal para que el programa corra localmente:

### 1. Clonar el repositorio
```powershell
git clone https://github.com/AlbertoLyonsZambra/scientific-research.git
cd scientific-research
```

### 2. Configurar Variables de Entorno (Importante)
El programa usa un archivo `.env` para saber a qué base de datos conectarse. 
Por defecto viene un `.env.example`. Sólo tienes que renombrarlo haciendo una copia local:

```powershell
cp .env.example .env
```
_Por defecto, el `.env` está pre-configurado para guardar todo automáticamente en una pequeña base de datos `SQLite` local, por lo que arrancará de inmediato sin necesitar instalaciones extras._

### 3. Crear entorno y Descargar Dependencias
Debemos levantar un entorno local para no ensuciar el Python de tu sistema e instalar bibliotecas (como Pandas y Selenium):

1. **Permitir usar Entornos desde PowerShell (Ejecutar solo una vez en la vida si arroja error el paso 2):**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
2. **Crear y activar entorno:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. **Instalar los Requerimientos:**
   ```powershell
   pip install -r requirements.txt
   ```

---

## 🖥 Uso del Web Scrapper

¡Listo! Para comenzar a bajar registros desde cualquier fecha o región en el mundo solamente ejecuta:
```powershell
python main.py
```

El programa te pedirá las variables necesarias interactivamente, abrirá internet en segundo plano, recuperará los registros de la capa tectónica solicitada e informará su inserción en tu Base de Datos local.

**Para corroborar que se insertaron bien los sismos extraídos:**
```powershell
python view_data.py
```