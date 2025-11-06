import numpy as np
from app.utils.config import LATENCY_WINDOW

def record_latency(start_time, end_time):
    latency = (end_time - start_time) * 1000
    LATENCY_WINDOW.append(latency)
    return latency

def average_latency():
    return float(np.mean(LATENCY_WINDOW)) if LATENCY_WINDOW else None
