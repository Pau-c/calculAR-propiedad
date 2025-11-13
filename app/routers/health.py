from fastapi import APIRouter
from app.utils.config import MODEL_PATH
from app.utils.latency import average_latency
from app.utils.model_loader import get_model
from app.utils.log_config import logger

router = APIRouter(prefix="/v1/health", tags=["Estado"])

@router.get("/")
def health_check():
    """
    Verifica el estado de la API y si el modelo está cargado en memoria.
    """
    model = None
    try:
        model = get_model()
    except Exception as e:
        
        logger.warning(f"Health check: No se pudo obtener el modelo: {e}")
        
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
        "avg_latency_ms": average_latency(),
    }