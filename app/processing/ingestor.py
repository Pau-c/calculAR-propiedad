import duckdb
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timezone
import glob
import re
from app.utils.log_config import logger

# --- CONFIGURACIÓN DE RUTAS Y DATOS ---
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

# Cargar variables de entorno desde .env
load_dotenv()


# --- FUNCIONES AUXILIARES DE INGESTA (SIN KAGGLE) ---
def ensure_directories():
    """Crea los directorios necesarios si no existen."""
    logger.info("Asegurando directorios de datos...")
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PARQUET_DIR, exist_ok=True)
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)


def find_latest_local_versioned_file(pattern: str, date_format: str):
    """Busca el archivo versionado más reciente según el nombre."""
    latest_date = None
    latest_file = None
    date_pattern = re.compile(rf"{KAGGLE_FILE_BASE}-(\d{{4}}-\d{{2}}-\d{{2}})\.csv")

    for filepath in glob.glob(pattern):
        match = date_pattern.search(os.path.basename(filepath))
        if match:
            date_str = match.group(1)
            try:
                file_date = datetime.strptime(date_str, date_format).replace(
                    tzinfo=timezone.utc
                )
                if latest_date is None or file_date > latest_date:
                    latest_date = file_date
                    latest_file = filepath
            except ValueError:
                logger.warning(f"Ignorando {filepath} (formato de fecha no válido).")
    return latest_file, latest_date


def run_duckdb_pipeline(csv_path_to_load: str):
    """Carga el CSV en DuckDB (datos_raw) y genera un Parquet."""
    if not os.path.exists(csv_path_to_load):
        logger.error(f"ERROR: No existe {csv_path_to_load}.")
        raise FileNotFoundError(
            f"Archivo CSV no encontrado en la ruta: {csv_path_to_load}"
        )

    logger.info(f"Conectando a DuckDB en {DB_PATH}...")
    try:
        con = duckdb.connect(DB_PATH)
        con.execute(
            f"""
            CREATE OR REPLACE TABLE datos_raw AS 
            SELECT * FROM read_csv_auto('{csv_path_to_load}')
            """
        )
        logger.info("Tabla 'datos_raw' actualizada.")

        con.execute(
            f"""
            COPY (
                SELECT * FROM datos_raw
            ) TO '{PARQUET_PATH}' (FORMAT PARQUET, OVERWRITE_OR_IGNORE TRUE)
            """
        )
        logger.info(f"Parquet generado en {PARQUET_PATH}.")
    except Exception as e:
        logger.error(f"Error durante el pipeline de DuckDB: {e}")
        raise
    finally:
        if "con" in locals():
            con.close()


# --- LÓGICA DE KAGGLE (ENVUELTA EN UNA FUNCIÓN LLAMABLE) ---
def _kaggle_api_logic(local_filepath: str | None, local_date: datetime | None) -> tuple[str | None, bool]:
    """
    Contiene TODA la lógica que requiere la API de Kaggle y la función requests.
    Solo se llama si el archivo legacy no existe.
    Devuelve: (file_to_process, needs_db_update)
    """
    import requests
    from requests.auth import HTTPBasicAuth
    import json
    from kaggle.api.kaggle_api_extended import KaggleApi

    def get_kaggle_dataset_update_time(dataset_slug: str) -> datetime | None:
        """Obtiene la fecha de última actualización (UTC) del dataset en Kaggle."""
        logger.info("Verificando disponibilidad de credenciales Kaggle...")

        try:
            username = os.getenv("KAGGLE_USERNAME")
            key = os.getenv("KAGGLE_KEY")

            kaggle_json_path = os.path.expanduser("~/.kaggle/kaggle.json")
            if not (username and key) and os.path.exists(kaggle_json_path):
                try:
                    with open(kaggle_json_path, "r") as f:
                        creds = json.load(f)
                        username = creds.get("username")
                        key = creds.get("key")
                except Exception as e:
                    logger.warning(f"No se pudo leer {kaggle_json_path}: {e}")

            if not (username and key):
                logger.warning(
                    "⚠️ No hay credenciales de Kaggle disponibles. Se omitirá la descarga."
                )
                return None

            logger.info("Consultando la API de Kaggle para verificar actualizaciones...")
            url = f"https://www.kaggle.com/api/v1/datasets/view/{dataset_slug}"
            response = requests.get(url, auth=HTTPBasicAuth(username, key))
            response.raise_for_status()
            metadata = response.json()
            kaggle_date_str = metadata.get("lastUpdated")

            if kaggle_date_str:
                for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
                    try:
                        return datetime.strptime(kaggle_date_str, fmt).replace(
                            tzinfo=timezone.utc
                        )
                    except ValueError:
                        continue
                logger.warning(
                    f"No se pudo interpretar la fecha 'lastUpdated': {kaggle_date_str}"
                )
            return None
        except Exception as e:
            logger.warning(f"No se pudo contactar con la API de Kaggle: {e}")
            return None

    def download_from_kaggle_and_rename(kaggle_time: datetime, date_format: str) -> str | None:
        """Descarga el dataset y lo renombra con la fecha."""
        from kaggle.api.kaggle_api_extended import KaggleApi

        date_str = kaggle_time.strftime(date_format) if kaggle_time else datetime.now().strftime(date_format)
        new_filename = f"{KAGGLE_FILE_BASE}-{date_str}.csv"
        new_filepath = os.path.join(RAW_DIR, new_filename)
        original_download_path = os.path.join(RAW_DIR, KAGGLE_FILE_NAME)

        logger.info(f"Descargando {KAGGLE_FILE_NAME} de Kaggle...")
        logger.info(f"Dataset URL: https://www.kaggle.com/datasets/{KAGGLE_DATASET}")

        try:
            api = KaggleApi()
            api.authenticate()  # ✅ importante: inicializa credenciales
            api.dataset_download_files(KAGGLE_DATASET, path=RAW_DIR, unzip=True, force=True)

            if not os.path.exists(original_download_path):
                logger.error(f"ERROR: No se encontró {original_download_path} después de descargar.")
                return None

            if os.path.exists(new_filepath):
                os.remove(new_filepath)

            os.rename(original_download_path, new_filepath)
            logger.info(f"Descarga completa y renombrada a {new_filepath}")
            return new_filepath

        except Exception as e:
            logger.error(f"ERROR: Falló la descarga de Kaggle: {e}")
            return None

    # --- Lógica de Decisión ---
    file_to_process = local_filepath
    needs_db_update = False
    kaggle_time = get_kaggle_dataset_update_time(KAGGLE_DATASET)

    if not kaggle_time:
        logger.warning("No se pudo obtener información de Kaggle (sin conexión o sin credenciales).")
        if not local_filepath:
            logger.error("No hay archivo CSV local disponible y no se puede descargar de Kaggle.")
            return None, False
        else:
            logger.info(f"Usando archivo local existente: {local_filepath}")
            return local_filepath, False

    elif not local_filepath:
        logger.info("No se encontró archivo local versionado. Descargando de Kaggle.")
        new_path = download_from_kaggle_and_rename(kaggle_time, DATE_FORMAT)
        if new_path:
            file_to_process = new_path
            needs_db_update = True

    elif kaggle_time.date() > local_date.date():
        logger.info(
            f"Nueva versión encontrada en Kaggle (Kaggle: {kaggle_time.date()}, Local: {local_date.date()}). Descargando..."
        )
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
        logger.info(
            f"El archivo local ({local_filepath}) está actualizado (Fecha: {local_date.date()})."
        )
        needs_db_update = False

    return file_to_process, needs_db_update


# --- FUNCIÓN PRINCIPAL DE INGESTA ---
async def run_ingestion_pipeline():
    """Punto de entrada principal para ejecutar todo el pipeline de ingesta."""
    logger.info("--- Iniciando Pipeline de Ingesta ---")

    file_to_process = None
    needs_db_update = False

    try:
        ensure_directories()

        #  Chequear si existe el archivo legacy (sin fecha)
        if os.path.exists(LEGACY_CSV_PATH):
            logger.info(f"Se encontró el archivo legacy '{LEGACY_CSV_PATH}'. Usando este archivo.")
            file_to_process = LEGACY_CSV_PATH
            needs_db_update = True
        else:
            #  Si no hay legacy, entra en la lógica de versión/descarga
            local_filepath, local_date = find_latest_local_versioned_file(
                VERSIONED_CSV_PATTERN, DATE_FORMAT
            )

            file_to_process, needs_db_update = _kaggle_api_logic(
                local_filepath, local_date
            )

            if not file_to_process:
                msg = "Proceso abortado. No hay archivo CSV disponible para procesar."
                logger.error(msg)
                return {"status": "error", "message": msg}

        # --- Ejecución Final ---
        if file_to_process and needs_db_update:
            logger.info("Actualizando DuckDB y Parquet...")
            run_duckdb_pipeline(file_to_process)
            message = "Ingesta completada. DuckDB y Parquet actualizados."
        elif file_to_process:
            logger.info(f"El archivo {file_to_process} está actualizado. No se requiere actualización de DB.")
            message = "Proceso finalizado. Los datos ya estaban actualizados."
        else:
            message = "Error en la ingesta. No hay CSV disponible."
            return {"status": "error", "message": message}

        logger.info("--- Pipeline de Ingesta Finalizado ---")
        return {"status": "ok", "message": message, "processed_file": file_to_process}

    except Exception as e:
        error_msg = f"Error fatal en el pipeline de ingesta: {e}"
        logger.error(error_msg, exc_info=True)
        return {"status": "error", "message": error_msg}
