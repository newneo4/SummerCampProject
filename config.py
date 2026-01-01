"""
Configuración de la aplicación de detección de objetos para ciegos.
"""

GEMINI_API_KEY = "AIzaSyDxsymE8a1LUICLWVPHgZGZywn_ESs2Y7g"

DANGEROUS_OBJECTS = {
    "car": 10,
    "truck": 10,
    "bus": 10,
    "motorcycle": 9,
    "bicycle": 7,
    
    "person": 5,
    "dog": 6,
    "cat": 4,
    "horse": 7,
    
    "chair": 3,
    "bench": 3,
    "fire hydrant": 4,
    "stop sign": 2,
    "parking meter": 3,
    "suitcase": 3,
    "backpack": 2,
}

PROXIMITY_THRESHOLDS = {
    "muy_cerca": 0.15,  
    "cerca": 0.08,       
    "medio": 0.03,       
}

VOICE_MESSAGES = {
    "ALTO": "¡Cuidado! {objeto} muy cerca, peligro alto",
    "MEDIO": "Atención, {objeto} adelante",
    "BAJO": "{objeto} detectado a distancia",
}

ALERT_COOLDOWN = 2.0

VOICE_RATE = 180  
VOICE_VOLUME = 1.0

CONFIDENCE_THRESHOLD = 0.5  
MODEL_NAME = "yolov8n.pt"  

DANGER_COLORS = {
    "ALTO": (0, 0, 255),    
    "MEDIO": (0, 165, 255),  
    "BAJO": (0, 255, 0),   
}
