from fastapi import APIRouter, BackgroundTasks, status, HTTPException
from app.processing.ingestor import run_ingestion_pipeline
from app.processing.trainer import run_training_pipeline
from app.utils.log_config import logger

router = APIRouter(prefix="/v1/pipeline", tags=["Pipeline Completo"])

def run_full_pipeline_task():
    """
    Tarea de orquestación que se ejecuta en segundo plano.
    Paso 1: Ejecutar la ingesta de datos.
    Paso 2: Ejecutar el entrenamiento usando los datos de la ingesta del paso 1
    """
    try:
        logger.info("--- INICIO: Pipeline de Configuración Completa ---")
        
        #   INGESTA 
        logger.info("Pipeline (Paso 1/2): Iniciando ingesta de datos...")
        ingest_result = run_ingestion_pipeline()
        logger.info(f"Pipeline (Paso 1/2): Ingesta completa. Mensaje: {ingest_result.get('message')}")

        if ingest_result.get("status") == "error":
             logger.error("Error en ingesta. Exit entrenamiento.")
             return

        #   ENTRENAMIENTO 
        logger.info("Pipeline (Paso 2/2): Iniciando entrenamiento del modelo...")
        train_result = run_training_pipeline()
        logger.info(f"Pipeline (Paso 2/2): Entrenamiento completado. Mensaje: {train_result.get('message')}")
        
        logger.info("--- FIN: Pipeline de Configuración Completa ---")

    except Exception as e:
        logger.error(f"Error fatal durante la ejecución del pipeline completo: {e}", exc_info=True)


@router.post("/ingest-train", status_code=status.HTTP_202_ACCEPTED, operation_id="run_full_pipeline_post")
def trigger_full_pipeline(background_tasks: BackgroundTasks):
    """
    Inicia el pipeline Ingesta/Entrenamiento en segundo plano, demora entre 5 a 10 min.
    Monitorear desde terminal y luego pasar al endpoint Predict
    
    """
    try:
        logger.info("Endpoint ingesta/entrenamiento activado. Añadiendo tarea en segundo plano.")
        background_tasks.add_task(run_full_pipeline_task)
        
        return {
            "status": "ok", 
            "message": "Proceso de ingesta y entrenamiento iniciado en segundo plano. Revise los logs."
        }
    except Exception as e:
        logger.error(f"Error al iniciar la tarea del pipeline completo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar la tarea: {e}"
        )