from fastapi import APIRouter, HTTPException
import time
import pandas as pd
import numpy as np
from app.models.schemas import Sample, PredictionOut
from app.utils.model_loader import load_model
from app.utils.latency import record_latency
from app.utils.log_config import logger 

#endpoint de predicción

router = APIRouter(prefix="/v1/predict", tags=["Predicciones"])
model = load_model()


@router.post("/", response_model=PredictionOut, operation_id="predict_price_post")
def predict(sample: Sample):
    start_time = time.time()

    logger.info(f"Nueva predicción: {sample.model_dump()}")

    input_df = pd.DataFrame([sample.model_dump()])
    
    # Ejecutar la predicción
    prediction = model.predict(input_df)[0]
    
    latency = record_latency(start_time, time.time())

    # Si la predicción no es válida da 422 
    if not np.isfinite(prediction) or prediction <= 0 or prediction > 1e9:
        logger.warning(f"Precio fuera de rango detectado: {prediction}")
      
        #   capturada por 'http_exception_handler'
        raise HTTPException(
            status_code=422, 
            detail=f"El modelo generó un precio fuera de rango: {prediction}"
        )

    result = PredictionOut(
        predicted_price=round(float(prediction), 2),
        currency=sample.currency,
        latency_ms=round(latency, 3),
    )

    logger.info(f"Predicción exitosa: {result.model_dump(mode='json')}")
    return result