from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os



# Importar todos los routers
from app.routers import health, predict, ingestion, training, pipeline
from app.utils.log_config import logger
from app.utils.model_loader import load_model
# Importar manejo de  excepciones
from app.exception_handlers import register_exception_handlers

load_dotenv()
app = FastAPI(
    title="API de Predicción de Precios de Propiedades",
    description="Una API para servir predicciones inmobiliarias",
    version="1.0.0"
)

# Event handlers 
@app.on_event("startup")
def startup_event():
    """
    Carga el modelo al iniciar la aplicación (si existe).
    Maneja el error si el modelo no se encuentra.
    """
    logger.info("Iniciando aplicación FastAPI...")
    try:
        load_model() # Carga el modelo en caché al iniciar
    except Exception as e:
        # Si el modelo no existe, solo registra una advertencia pero permite que la API continúe.
        logger.warning(f"Startup: No se pudo cargar el modelo al inicio: {e}")
        logger.warning("La API se iniciará sin un modelo cargado. Ejecute el endpoint de entrenamiento/pipeline.")


# Registra los manejadores personalizados (de exception_handlers.py)
register_exception_handlers(app)


# --- Inclusión de Routers ---
logger.info("Incluyendo routers...")
app.include_router(health.router)
# Ruta que fusiona ingesta y entrenamiento
app.include_router(pipeline.router)
app.include_router(predict.router)
#endpoints de ingesta y entrenamiento separados
app.include_router(ingestion.router)
app.include_router(training.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)