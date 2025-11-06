from collections import deque

''''
registra la latencia cada solicitud y lo añade a la cola, solo almacena
los últimos 50 valores. Si se agrega un valor nuevo, el  más viejo
se descarta automáticamente.
'''
MODEL_PATH = "app/data/housing_models/random_forest.joblib"
LATENCY_WINDOW = deque(maxlen=50)
