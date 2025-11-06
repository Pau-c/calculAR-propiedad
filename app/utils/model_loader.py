import joblib
from app.utils.config import MODEL_PATH

# carga modelo guardado por joblib

def load_model():
    try:
        model = joblib.load(MODEL_PATH)
        return model
    except Exception as e:
        raise RuntimeError(f"Error cargando el modelo: {e}")
