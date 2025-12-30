"""
Configuración de la aplicación de detección de objetos para ciegos.
"""

# API Key de Gemini (Hardcoded por solicitud del usuario)
GEMINI_API_KEY = "AIzaSyDxsymE8a1LUICLWVPHgZGZywn_ESs2Y7g"

# Objetos peligrosos y su nivel de amenaza base (1-10)
DANGEROUS_OBJECTS = {
    # Vehículos - Muy peligrosos
    "car": 10,
    "truck": 10,
    "bus": 10,
    "motorcycle": 9,
    "bicycle": 7,
    
    # Personas y animales
    "person": 5,
    "dog": 6,
    "cat": 4,
    "horse": 7,
    
    # Objetos estáticos potencialmente peligrosos
    "chair": 3,
    "bench": 3,
    "fire hydrant": 4,
    "stop sign": 2,
    "parking meter": 3,
    "suitcase": 3,
    "backpack": 2,
}

# Umbrales de área relativa para determinar cercanía
# (área del bbox / área total de la imagen)
PROXIMITY_THRESHOLDS = {
    "muy_cerca": 0.15,   # >15% del frame = muy cerca
    "cerca": 0.08,       # >8% del frame = cerca
    "medio": 0.03,       # >3% del frame = distancia media
}

# Mensajes de voz por nivel de peligro
VOICE_MESSAGES = {
    "ALTO": "¡Cuidado! {objeto} muy cerca, peligro alto",
    "MEDIO": "Atención, {objeto} adelante",
    "BAJO": "{objeto} detectado a distancia",
}

# Cooldown en segundos entre alertas del mismo tipo
ALERT_COOLDOWN = 2.0

# Configuración de voz
VOICE_RATE = 180  # Palabras por minuto
VOICE_VOLUME = 1.0  # 0.0 a 1.0

# Configuración de detección
CONFIDENCE_THRESHOLD = 0.5  # Mínimo 50% de confianza
MODEL_NAME = "yolov8n.pt"  # Modelo nano (más rápido)

# Colores para visualización (BGR)
DANGER_COLORS = {
    "ALTO": (0, 0, 255),    # Rojo
    "MEDIO": (0, 165, 255),  # Naranja
    "BAJO": (0, 255, 0),     # Verde
}
