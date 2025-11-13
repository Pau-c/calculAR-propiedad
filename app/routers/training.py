from fastapi import APIRouter, BackgroundTasks, status, HTTPException
from app.processing.trainer import run_training_pipeline
from app.utils.log_config import logger

router = APIRouter(prefix="/v1/train", tags=["Entrenamiento"])
 # Los docstring se muestra en localhost
@router.post("/", status_code=status.HTTP_202_ACCEPTED, operation_id="trigger_training_post")
def trigger_training(background_tasks: BackgroundTasks):
    """
    Inicia el proceso de entrenamiento de modelos (Carga -> Limpieza -> FE -> Train -> Save).
    Este proceso se ejecuta en segundo plano, ya que demora un poco. Seguir el proceso mirando la informacion de la terminal
    """
    try:
        logger.info("Endpoint /v1/train llamado. Añadiendo tarea en segundo plano.")
        # entrenamiento como una tarea en segundo plano
        background_tasks.add_task(run_training_pipeline)
        
        return {
            "status": "ok", 
            "message": "Proceso de entrenamiento iniciado en segundo plano. Revise los logs para ver el estado."
        }
    except Exception as e:
        logger.error(f"Error al iniciar la tarea de entrenamiento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar la tarea de entrenamiento: {e}"
        )