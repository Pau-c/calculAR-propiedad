from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import joblib
import time
import numpy as np
from collections import deque
import pandas as pd

# =========================================================
# CONFIGURACIÓN Y CARGA DE MODELO
# =========================================================

MODEL_PATH = "data/housing_models/random_forest.joblib"  # elegir modelo guardado
model = joblib.load(MODEL_PATH)

# guarda latencia para /health
latency_window = deque(maxlen=50)


# =========================================================
# Pydantic models
# =========================================================
class Sample(BaseModel):
    lon: float = Field(..., description="Longitud geográfica")
    lat: float = Field(..., description="Latitud geográfica")
    l3: str = Field(..., description="Barrio o zona (ej: Almagro)")
    rooms: Optional[float] = Field(None, ge=0)
    bedrooms: Optional[float] = Field(None, ge=0)
    bathrooms: Optional[float] = Field(None, ge=0)
    surface_total: Optional[float] = Field(None, ge=0)
    surface_covered: Optional[float] = Field(None, ge=0)
    currency: str = Field("USD", description="Moneda de precio esperado")
    price_period: Optional[str] = Field(
        None, description="Periodo del precio (si aplica)"
    )
    property_type: str = Field(
        ..., description="Tipo de propiedad (ej: Departamento, PH, Casa)"
    )
    operation_type: str = Field(
        ..., description="Tipo de operación (ej: Venta, Alquiler)"
    )
    days_active: Optional[float] = Field(None, ge=0)
    created_age_days: Optional[float] = Field(None, ge=0)

    # ejemplo para endpoint en swagger /docs por default
    model_config = {
        "json_schema_extra": {
            "example": {
                "lon": -58.42,
                "lat": -34.61,
                "l3": "Almagro",
                "rooms": 3,
                "bedrooms": 1,
                "bathrooms": 1,
                "surface_total": 100,
                "surface_covered": 50,
                "currency": "USD",
                "price_period": None,
                "property_type": "Departamento",
                "operation_type": "Venta",
                "days_active": None,
                "created_age_days": None,
            }
        }
    }


class PredictionOut(BaseModel):
    predicted_price: float
    currency: str
    latency_ms: float


# =========================================================
# APP FastAPI
# =========================================================


app = FastAPI(title="calculAR ML API", version="1.0")


@app.get("/health")
def health_check():
    """
    Retorna estado del modelo y métricas
    Incluye latencia promedio de las últimas predicciones
    """
    avg_latency = float(np.mean(latency_window)) if latency_window else None
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
        "avg_latency_ms": avg_latency,
        "recent_predictions_count": len(latency_window),
    }


@app.post("/predict", operation_id="predict_price_post")
def predict(sample: Sample):
    start_time = time.time()
    input_df = pd.DataFrame([sample.dict()])
    prediction = model.predict(input_df)[0]

    # Validar rango
    if not np.isfinite(prediction) or prediction <= 0 or prediction > 1e9:
        raise HTTPException(
            status_code=422, detail=f"Precio fuera de rango: {prediction}"
        )

    end_time = time.time()
    latency = (end_time - start_time) * 1000
    latency_window.append(latency)

    return PredictionOut(
        predicted_price=round(float(prediction), 2),
        currency=sample.currency,
        latency_ms=round(latency, 3),
    )
