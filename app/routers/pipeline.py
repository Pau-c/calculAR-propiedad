from fastapi import APIRouter, BackgroundTasks, status, HTTPException
from app.processing.ingestor import run_ingestion_pipeline
from app.processing.trainer import run_training_pipeline
from app.utils.log_config import logger
# (Imports de task_manager y typing eliminados)

router = APIRouter(prefix="/v1/pipeline", tags=["Pipeline Completo"])

async def run_full_pipeline_task():
    """
    Tarea de orquestación que se ejecuta en segundo plano.
    (Versión simplificada sin monitor de estado)
    """
    try:
        logger.info("--- INICIO: Pipeline de Configuración Completa ---")
        
        # --- PASO 1: INGESTA ---
        logger.info("Pipeline (Paso 1/2): Iniciando ingesta de datos...")
        
        # Esta es la corrección clave: 'await'
        ingest_result = await run_ingestion_pipeline()
        
        # Comprobación de que ingest_result es un diccionario (y no una corutina no esperada)
        if isinstance(ingest_result, dict):
            logger.info(f"Pipeline (Paso 1/2): Ingesta completada. Mensaje: {ingest_result.get('message')}")
            if ingest_result.get("status") == "error":
                 logger.error("Error en el paso de ingesta. Abortando el entrenamiento.")
                 return
        else:
             logger.warning(f"La ingesta no devolvió un diccionario. Resultado: {ingest_result}")


        # --- PASO 2: ENTRENAMIENTO ---
        logger.info("Pipeline (Paso 2/2): Iniciando entrenamiento del modelo...")
        
        # Esta es la corrección clave: 'await'
        train_result = await run_training_pipeline()
        
        if isinstance(train_result, dict):
            logger.info(f"Pipeline (Paso 2/2): Entrenamiento completado. Mensaje: {train_result.get('message')}")
        
        logger.info("--- FIN: Pipeline de Configuración Completa ---")

    except Exception as e:
        error_msg = f"Error fatal durante la ejecución del pipeline completo: {e}"
        logger.error(error_msg, exc_info=True)
        # (Llamadas a set_task_status eliminadas)


@router.post("/ingest-train", status_code=status.HTTP_202_ACCEPTED, operation_id="run_full_pipeline_post")
def trigger_full_pipeline(background_tasks: BackgroundTasks):
    """
    Inicia el pipeline completo (Ingesta Y Entrenamiento) en segundo plano.
    
    
    """
    try:
        logger.info("Endpoint /v1/pipeline/ingest-train llamado. Añadiendo tarea en segundo plano.")
        background_tasks.add_task(run_full_pipeline_task)
        
        return {
            "status": "ok", 
            # Mensaje actualizado:
            "message": "Proceso de ingesta y entrenamiento iniciado en segundo plano. Revise los logs para el estado."
        }
    except Exception as e:
        logger.error(f"Error al iniciar la tarea del pipeline completo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar la tarea: {e}"
        )

# --- ENDPOINT DE MONITOR DE ESTADO (ELIMINADO) ---