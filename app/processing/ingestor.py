import duckdb
import os
import pandas as pd
from dotenv import load_dotenv
from kaggle.api.kaggle_api_extended import KaggleApi
from datetime import datetime, timezone
import glob
import re
from app.utils.log_config import logger 
import requests
from requests.auth import HTTPBasicAuth
import json

#  CONFIGURACIÓN DE RUTAS Y DATOS 

DB_PATH = "app/data/DB/entrenamiento.duckdb"
RAW_DIR = "app/data/artifacts/RAW"
PARQUET_DIR = "app/data/artifacts/parquet"
PARQUET_PATH = os.path.join(PARQUET_DIR, "entrenamiento.parquet")

LEGACY_CSV_PATH = os.path.join(RAW_DIR, "entrenamiento.csv") 

KAGGLE_FILE_BASE = "entrenamiento"
VERSIONED_CSV_PATTERN = os.path.join(RAW_DIR, f"{KAGGLE_FILE_BASE}-*.csv")
DATE_FORMAT = "%Y-%m-%d"

KAGGLE_DATASET = "alejandroczernikier/properati-argentina-dataset"
KAGGLE_FILE_NAME = "entrenamiento.csv"

load_dotenv()

#  Funciones de Ingesta 

def ensure_directories():
    logger.info("chequeando directorios de datos...")
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PARQUET_DIR, exist_ok=True)
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)

def find_latest_local_versioned_file(pattern: str, date_format: str):
    latest_date = None
    latest_file = None
    date_pattern = re.compile(rf'{KAGGLE_FILE_BASE}-(.*)\.csv')

    try:
        for filepath in glob.glob(pattern):
            match = date_pattern.search(os.path.basename(filepath))
            if match:
                date_str = match.group(1)
                try:
                    file_date = datetime.strptime(date_str, date_format).replace(tzinfo=timezone.utc)
                    if latest_date is None or file_date > latest_date:
                        latest_date = file_date
                        latest_file = filepath
                except ValueError:
                    logger.warning(f"Ignorando {filepath} (formato de fecha no válido).")
        return latest_file, latest_date
    except Exception as e:
        logger.error(f"Error al buscar archivos locales versionados: {e}")
        return None, None


# Kaggle
def get_kaggle_dataset_update_time(dataset_slug: str):
    """Obtiene la fecha de última actualización (UTC) del *dataset* en Kaggle."""
    logger.info("Contacto con API de Kaggle para verificar la última actualización del dataset...")
    
    try:
        api = KaggleApi()
        api.authenticate() # Asegura que kaggle.json esté cargado

        username = os.getenv("KAGGLE_USERNAME")
        key = os.getenv("KAGGLE_KEY")

        # si no está en el entorno, leer desde kaggle.json 
        if not username or not key:
            kaggle_json_path = os.path.expanduser("~/.kaggle/kaggle.json")
            if os.path.exists(kaggle_json_path):
                with open(kaggle_json_path, "r") as f:
                    creds = json.load(f)
                    username = creds.get("username")
                    key = creds.get("key")

        if not username or not key:
            raise ValueError("Faltan credenciales KAGGLE_USERNAME o KAGGLE_KEY en el entorno o kaggle.json.")

        url = f"https://www.kaggle.com/api/v1/datasets/view/{dataset_slug}"
        response = requests.get(url, auth=HTTPBasicAuth(username, key))
        response.raise_for_status() # Lanza error si la API falla
        metadata = response.json()

        kaggle_date_str = metadata.get("lastUpdated")
        if kaggle_date_str:
            # Probar múltiples formatos de fecha que Kaggle puede enviar
            for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
                try:
                    kaggle_date = datetime.strptime(kaggle_date_str, fmt).replace(tzinfo=timezone.utc)
                    logger.info(f"Fecha de última actualización en Kaggle: {kaggle_date}")
                    return kaggle_date
                except ValueError:
                    continue
        logger.warning("No se pudo interpretar la fecha 'lastUpdated' de la API de Kaggle.")
        return None

    except Exception as e:
        logger.error(f"Fallo al contactar la API de Kaggle: {e}", exc_info=True)
        return None


def download_from_kaggle_and_rename(kaggle_time: datetime, date_format: str):
    date_str = kaggle_time.strftime(date_format)
    new_filename = f"{KAGGLE_FILE_BASE}-{date_str}.csv"
    new_filepath = os.path.join(RAW_DIR, new_filename)
    original_download_path = os.path.join(RAW_DIR, KAGGLE_FILE_NAME)

    logger.info(f"Descargando {KAGGLE_FILE_NAME} de Kaggle...")
    try:
        api = KaggleApi()
        api.authenticate()
        
        api.dataset_download_files(
            KAGGLE_DATASET,
            path=RAW_DIR,
            unzip=True,
            force=True
        )
        
        if os.path.exists(new_filepath):
             os.remove(new_filepath)
             
        os.rename(original_download_path, new_filepath)
            
        logger.info(f"Descarga exitosa. Archivo guardado como: {new_filepath}")
        return new_filepath

    except Exception as e:
        logger.error(f"Fallo en la descarga de Kaggle: {e}")
        return None

def run_duckdb_pipeline(csv_path_to_load: str):
    if not os.path.exists(csv_path_to_load):
        logger.error(f"El archivo CSV {csv_path_to_load} no existe. Exit DuckDB.")
        return

    logger.info(f"Iniciando conexión con DuckDB en {DB_PATH}...")
    try:
        with duckdb.connect(DB_PATH) as con:
            logger.info(f"Creando/reemplazando tabla 'datos_raw' desde {csv_path_to_load}...")
            con.execute(f"""
                CREATE OR REPLACE TABLE datos_raw AS 
                SELECT * FROM read_csv_auto('{csv_path_to_load}')
            """)
            logger.info("Tabla 'datos_raw' creada/reemplazada.")

            logger.info(f"Guardando Parquet en {PARQUET_PATH}...")
            con.execute(f"""
                COPY (SELECT * FROM datos_raw) 
                TO '{PARQUET_PATH}' (FORMAT PARQUET, OVERWRITE_OR_IGNORE TRUE)
            """)
            logger.info("Archivo Parquet generado/actualizado.")

    except duckdb.DuckDBError as e:
        logger.error(f"ERROR de DuckDB: {e}")

# --- FUNCIÓN PRINCIPAL DE INGESTA ---
def run_ingestion_pipeline():
    """
    Punto de entrada principal para ejecutar todo el pipeline de ingesta.
    """
    logger.info("--- Iniciando Pipeline de Ingesta ---")
    ensure_directories()
    
    file_to_process = None
    needs_db_update = False 
    
    if os.path.exists(LEGACY_CSV_PATH):
        logger.info(f"Se encontró el archivo legacy '{LEGACY_CSV_PATH}'. Usando este archivo.")
        file_to_process = LEGACY_CSV_PATH
        needs_db_update = True 
    else:
        logger.info("No se encontró archivo legacy. Buscando archivos versionados...")
        local_filepath, local_date = find_latest_local_versioned_file(VERSIONED_CSV_PATTERN, DATE_FORMAT)
        
        kaggle_time = get_kaggle_dataset_update_time(KAGGLE_DATASET)
        
        if not kaggle_time:
            logger.error("No se pudo contactar a Kaggle.")
            if local_filepath:
                logger.info(f"Se usará el archivo local más reciente: {local_filepath}")
                file_to_process = local_filepath
                needs_db_update = False # Asumimos que ya está en DB
            else:
                logger.error("No hay archivo local ni conexión a Kaggle. Exit ingesta.")
                return {"status": "error", "message": "No hay archivo local ni conexión a Kaggle."}
        
        elif not local_filepath:
            logger.info("No se encontró archivo local versionado. Descargando de Kaggle.")
            new_path = download_from_kaggle_and_rename(kaggle_time, DATE_FORMAT)
            if new_path:
                file_to_process = new_path
                needs_db_update = True 
                
        elif kaggle_time.date() > local_date.date():
            logger.info(f"Nueva versión encontrada en Kaggle (Kaggle: {kaggle_time.date()}, Local: {local_date.date()}). Descargando...")
            new_path = download_from_kaggle_and_rename(kaggle_time, DATE_FORMAT)
            if new_path:
                file_to_process = new_path
                needs_db_update = True 
                try:
                    os.remove(local_filepath)
                    logger.info(f"Archivo local antiguo ({local_filepath}) eliminado.")
                except OSError as e:
                    logger.warning(f"No se pudo eliminar el archivo antiguo {local_filepath}: {e}")
        else:
            logger.info(f"El archivo local ({local_filepath}) está actualizado.")
            file_to_process = local_filepath
            needs_db_update = False 

    #  Ejecución Final hacia DuckDB 
    if file_to_process and needs_db_update:
        logger.info(" cambio Detectado en el CSV. Actualizando DuckDB y Parquet...")
        run_duckdb_pipeline(file_to_process)
        message = "Ingesta completada. DuckDB y archivo Parquet actualizados."
    elif file_to_process:
        logger.info(f"El archivo {file_to_process} está actualizado. No se necesita de una actualización de DB.")
        message = "Proceso finalizado. Los datos ya estaban actualizados."
    else:
        logger.error("Error . No hay archivo CSV disponible para procesar.")
        message = "Error en la ingesta. No hay CSV disponible."

    logger.info("--- Pipeline de Ingesta Finalizado ---")
    return {"status": "ok", "message": message, "processed_file": file_to_process}