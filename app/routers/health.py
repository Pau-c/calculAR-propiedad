from fastapi import APIRouter
from app.utils.config import MODEL_PATH
from app.utils.latency import average_latency
# MODIFICACIÓN: Importar get_model en lugar de load_model
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
        # MODIFICACIÓN: Obtener el modelo desde la caché (o cargarlo si es la primera vez)
        model = get_model()
    except Exception as e:
        # Si get_model() falla (ej. el archivo aún no existe), lo manejamos
        logger.warning(f"Health check: No se pudo obtener el modelo: {e}")
        
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
        "avg_latency_ms": average_latency(),
    }