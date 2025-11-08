from fastapi import FastAPI
from app.routers import health
import os
from app.utils.log_config import logger
from ddtrace import patch_all, tracer
from app.routers.predict import router as predict_router
from app.exception_handlers import register_exception_handlers 
from contextlib import asynccontextmanager

is_production = os.getenv("ENV") == "development"

#CAMBIAR A TRUE PARA ACTIVAR  DATADOG
tracer.enabled = False
patch_all()  #  activa auto-instrumentación


# oculta endpoints /docs en produccion
app = FastAPI(
    title="CalculAR $ Propiedades",
    version="1.0.0",
    description="API para predicción inmobiliaria",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json"
)

#EVENTOS INICIO/CIERRE 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # loguea inicio 
    logger.info("Aplicación FastAPI iniciada correctamente.")
    
    yield  # Aquí es donde la aplicación se ejecuta
    
    # loguea cierre 
    logger.info("Aplicación FastAPI cerrándose...")


# Routers
app.include_router(health.router)
app.include_router(predict_router)

#error handlers
register_exception_handlers(app)