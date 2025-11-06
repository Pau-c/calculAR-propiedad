from collections import deque
'''
Eleccion de modelo: load_model en model_loader.py -> model en predict.py
'''

MODEL_PATH = "app/data/artifacts/housing_models/random_forest.joblib"

''''
registra la latencia de cada solicitud y lo añade a la cola, solo almacena
los últimos 50 valores. Si se agrega un valor nuevo, el  más viejo
se descarta automáticamente.
'''

LATENCY_WINDOW = deque(maxlen=50)
