"""
Módulo de evaluación de nivel de peligro.
"""

from dataclasses import dataclass
from typing import Optional
from detector import Detection
import config


@dataclass
class DangerAssessment:
    """Evaluación de peligro de un objeto detectado."""
    detection: Detection
    danger_level: str  
    danger_score: float
    message: str


class DangerAssessor:
    """Evalúa el nivel de peligro de objetos detectados."""
    
    def assess(self, detection: Detection, frame_width: int) -> Optional[DangerAssessment]:
        """
        Evalúa el nivel de peligro de una detección.
        
        Args:
            detection: Objeto detectado
            frame_width: Ancho del frame para calcular posición
            
        Returns:
            Evaluación de peligro o None si el objeto no es relevante
        """
        base_danger = config.DANGEROUS_OBJECTS.get(detection.class_name, 1)
        
        proximity_multiplier = self._get_proximity_multiplier(detection.relative_area)
        
        position_multiplier = self._get_position_multiplier(
            detection.center[0], frame_width
        )
        
        danger_score = min(100, base_danger * proximity_multiplier * position_multiplier)
        
        if danger_score >= 60:
            danger_level = "ALTO"
        elif danger_score >= 30:
            danger_level = "MEDIO"
        else:
            danger_level = "BAJO"
        
        message = config.VOICE_MESSAGES[danger_level].format(
            objeto=self._translate_object(detection.class_name)
        )
        
        return DangerAssessment(
            detection=detection,
            danger_level=danger_level,
            danger_score=danger_score,
            message=message
        )
    
    def _get_proximity_multiplier(self, relative_area: float) -> float:
        """Calcula multiplicador basado en cercanía."""
        if relative_area >= config.PROXIMITY_THRESHOLDS["muy_cerca"]:
            return 10.0
        elif relative_area >= config.PROXIMITY_THRESHOLDS["cerca"]:
            return 6.0
        elif relative_area >= config.PROXIMITY_THRESHOLDS["medio"]:
            return 3.0
        else:
            return 1.0
    
    def _get_position_multiplier(self, center_x: int, frame_width: int) -> float:
        """
        Calcula multiplicador basado en posición horizontal.
        Objetos en el centro son más peligrosos (frente al usuario).
        """
        normalized_x = center_x / frame_width
        
        distance_from_center = abs(normalized_x - 0.5)
        
        return 1.5 - distance_from_center
    
    def _translate_object(self, class_name: str) -> str:
        """Traduce nombre de objeto al español."""
        translations = {
            "person": "persona",
            "car": "carro",
            "truck": "camión",
            "bus": "autobús",
            "motorcycle": "moto",
            "bicycle": "bicicleta",
            "dog": "perro",
            "cat": "gato",
            "horse": "caballo",
            "chair": "silla",
            "bench": "banco",
            "fire hydrant": "hidrante",
            "stop sign": "señal de alto",
            "parking meter": "parquímetro",
            "suitcase": "maleta",
            "backpack": "mochila",
            "bottle": "botella",
            "cup": "taza",
            "laptop": "laptop",
            "cell phone": "teléfono",
            "book": "libro",
            "clock": "reloj",
            "scissors": "tijeras",
            "teddy bear": "oso de peluche",
            "potted plant": "planta",
            "bed": "cama",
            "dining table": "mesa",
            "toilet": "inodoro",
            "tv": "televisor",
            "couch": "sofá",
            "umbrella": "paraguas",
        }
        return translations.get(class_name, class_name)
