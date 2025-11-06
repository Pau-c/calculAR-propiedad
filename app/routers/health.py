from fastapi import APIRouter
from app.utils.config import MODEL_PATH
from app.utils.latency import average_latency
from app.utils.model_loader import load_model

#endpoint de health 

router = APIRouter(prefix="/v1/health", tags=["Estado"])
model = load_model()

@router.get("/")
def health_check():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
        "avg_latency_ms": average_latency(),
    }
