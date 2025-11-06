from fastapi import FastAPI
from app.routers import predict, health

app = FastAPI(
    title="CalculAR $ Propiedades",
    version="1.0.0",
    description="API para predicción inmobiliaria"
)

# Routers
app.include_router(health.router)
app.include_router(predict.router)
