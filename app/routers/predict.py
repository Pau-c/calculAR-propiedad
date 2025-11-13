from fastapi import APIRouter, HTTPException, status
import time
import pandas as pd
import numpy as np
from app.models.schemas import Sample, PredictionOut
from app.utils.model_loader import get_model, load_model
from app.utils.latency import record_latency
from app.utils.log_config import logger 

router = APIRouter(prefix="/v1/predict", tags=["Predicciones"])
#  modelo se cargará en la primera petición

@router.post("/", response_model=PredictionOut, operation_id="predict_price_post")
def predict(sample: Sample):
    start_time = time.time()
    
    
    model = get_model() 
    
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo no cargado. Ejecute el entrenamiento o revise los logs."
        )

    logger.info(f"Nueva predicción: {sample.model_dump()}")
    input_df = pd.DataFrame([sample.model_dump()])
    
    try:
        prediction = model.predict(input_df)[0]
    except Exception as e:
        logger.error(f"Error durante la predicción: {e}")
        raise HTTPException(status_code=422, detail=f"Error al procesar la predicción: {e}")

    latency = record_latency(start_time, time.time())

    if not np.isfinite(prediction) or prediction <= 0 or prediction > 1e9:
        logger.warning(f"Precio fuera de rango detectado: {prediction}")
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

@router.post("/reload-model", status_code=status.HTTP_200_OK, operation_id="reload_model_post")
def reload_model():
    """
    Fuerza la recarga del modelo desde el disco (archivo .joblib) después de ejecutar un re-entrenamiento.
    """
    try:
        load_model(force_reload=True)
        return {"status": "ok", "message": "Modelo recargado exitosamente."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )