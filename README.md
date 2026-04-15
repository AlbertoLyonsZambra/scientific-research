# Scientific Research - Global CMT Scrapper

Este repositorio contiene un sistema automatizado para buscar, descargar y parsear bases de datos sismológicas masivas desde [Global CMT](https://www.globalcmt.org). Extrae automáticamente las propiedades científicas de los sismos basándose en variables controlables (tiempo y región en latitud/longitud) para poblar una base de datos local predefinida con Pandas y SQLAlchemy.

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