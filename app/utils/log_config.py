
from loguru import logger
import sys
import os
#LOGGER CONFIGURACION
# Crear carpeta de logs si no existe
os.makedirs("logs", exist_ok=True)

logger.remove()  # eliminar handlers previos

# Consola (para desarrollo)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    level="INFO",
)

# Archivo 
logger.add(
    "logs/app.log",
    rotation="1 week",
    retention="4 weeks",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

__all__ = ["logger"]

