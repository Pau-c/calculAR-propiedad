from fastapi import APIRouter, BackgroundTasks, status, HTTPException
from app.processing.ingestor import run_ingestion_pipeline
from app.utils.log_config import logger

router = APIRouter(prefix="/v1/ingest", tags=["Ingesta de Datos"])

@router.post("/", status_code=status.HTTP_202_ACCEPTED, operation_id="trigger_ingestion_post")
def trigger_ingestion(background_tasks: BackgroundTasks):
    """
    Inicia el proceso de ingesta de datos 
    Este proceso se ejecuta en segundo plano.
    """
    try:
        logger.info("Endpoint /v1/ingest llamado. Añadiendo tarea en segundo plano.")
        # Añade la función de ingesta como una tarea en segundo plano
        background_tasks.add_task(run_ingestion_pipeline)
        
        return {
            "status": "ok", 
            "message": "Proceso de ingesta iniciado en segundo plano. Revise los logs para ver el estado."
        }
    except Exception as e:
        logger.error(f"Error al iniciar la tarea de ingesta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar la tarea de ingesta: {e}"
        )