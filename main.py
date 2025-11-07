from fastapi import FastAPI
from app.routers import predict, health

# app = FastAPI(
#     title="CalculAR $ Propiedades",
#     version="1.0.0",
#     description="API para predicción inmobiliaria"
# )

import os

is_production = os.getenv("ENV") == "development"

# oculta endpoints /docs en produccion
app = FastAPI(
    title="CalculAR $ Propiedades",
    version="1.0.0",
    description="API para predicción inmobiliaria",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json"
)


# Routers
app.include_router(health.router)
app.include_router(predict.router)
