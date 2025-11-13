import joblib
from app.utils.config import MODEL_PATH
from app.utils.log_config import logger

# Variable global para mantener el modelo en caché
_model = None

def load_model(force_reload: bool = False):
    """
    Carga el modelo desde el archivo .joblib apuntado en config.py
    Si force_reload=True, vuelve a cargarlo del disco.
    """
    global _model
    
    if _model is not None and not force_reload:
        logger.info("Retornando modelo desde caché.")
        return _model

    try:
        logger.info(f"Cargando modelo desde: {MODEL_PATH}...")
        _model = joblib.load(MODEL_PATH)
        logger.info("Modelo cargado")
        return _model
    except Exception as e:
        logger.error(f"Error cargando el modelo: {e}")
        _model = None # Asegurarse que el modelo es None si falla la carga
        raise RuntimeError(f"Error cargando el modelo: {e}")

def get_model():
    """
    Obtiene el modelo cargado (lo carga si no está en caché).
    Esta es la función que deben usar los endpoints de predicción.
    """
    if _model is None:
        return load_model()
    return _model