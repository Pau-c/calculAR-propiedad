from fastapi import FastAPI
from app.routers import health
import os
from app.utils.log_config import logger
from ddtrace import patch_all
from app.routers.predict import router as predict_router
from app.exception_handlers import register_exception_handlers 
from contextlib import asynccontextmanager

is_production = os.getenv("ENV") == "development"

patch_all()  #  activa auto-instrumentación


#EVENTOS INICIO/CIERRE 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # loguea inicio 
    logger.info("Aplicación FastAPI iniciada correctamente.")
    
    yield  
    
    # loguea cierre 
    logger.info("Aplicación FastAPI cerrándose...")

# oculta endpoints /docs en produccion
app = FastAPI(
    title="CalculAR $ Propiedades",
    version="1.0.0",
    description="API para predicción inmobiliaria",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
    lifespan=lifespan 
)

# Routers
app.include_router(health.router)
app.include_router(predict_router)

#error handlers
register_exception_handlers(app)