
from loguru import logger
import sys
import os

# CONFIGURACION LOGGER
# Crear carpeta de logs si no existe
os.makedirs("logs", exist_ok=True)

logger.remove()  # eliminar handlers por defecto
log_format = os.getenv("LOG_FORMAT", "text")

 # --- MODO PRODUCCIÓN (JSON para Datadog) ---
    # Si LOG_FORMAT es "json", serializa los logs y  loguea a stdout 
if log_format == "json":
   
    logger.add(
        sys.stdout,
        serialize=True,  
        level="INFO",
        format="{time} {level} {message}",
    )
    logger.info("Configuración de logging en modo JSON activada.")
else:
    # --- MODO DESARROLLO : Si corre solo con uvicorn loguea en carpeta logs/app.log
    logger.info("logging en logs/app.log ")

# Consola 
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    level="INFO",
    colorize=True,
)

# persistencia .log
logger.add(
    "logs/app.log",
    rotation="1 week",
    retention="4 weeks",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

__all__ = ["logger"]

