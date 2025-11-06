from fastapi import APIRouter, HTTPException
import time
import pandas as pd
import numpy as np
from app.models.schemas import Sample, PredictionOut
from app.utils.model_loader import load_model
from app.utils.latency import record_latency

#endpoint de predicción

router = APIRouter(prefix="/v1/predict", tags=["Predicciones"])
model = load_model()

@router.post("/", response_model=PredictionOut, operation_id="predict_price_post")
def predict(sample: Sample):
    start_time = time.time()
    input_df = pd.DataFrame([sample.dict()])
    prediction = model.predict(input_df)[0]

    if not np.isfinite(prediction) or prediction <= 0 or prediction > 1e9:
        raise HTTPException(status_code=422, detail=f"Precio fuera de rango: {prediction}")

    latency = record_latency(start_time, time.time())

    return PredictionOut(
        predicted_price=round(float(prediction), 2),
        currency=sample.currency,
        latency_ms=round(latency, 3),
    )
