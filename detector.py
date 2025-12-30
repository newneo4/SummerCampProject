"""
Módulo de detección de objetos usando YOLOv8.
"""

from ultralytics import YOLO
import numpy as np
from dataclasses import dataclass
from typing import List
import config


@dataclass
class Detection:
    """Representa un objeto detectado."""
    class_name: str
    confidence: float
    bbox: tuple  # (x1, y1, x2, y2)
    center: tuple  # (cx, cy)
    relative_area: float  # Área relativa al frame


class ObjectDetector:
    """Detector de objetos usando YOLOv8."""
    
    def __init__(self):
        """Inicializa el modelo YOLO."""
        self.model = YOLO(config.MODEL_NAME)
        self.class_names = self.model.names
        
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detecta objetos en un frame.
        
        Args:
            frame: Imagen BGR de OpenCV
            
        Returns:
            Lista de detecciones
        """
        # Obtener dimensiones del frame
        frame_height, frame_width = frame.shape[:2]
        frame_area = frame_height * frame_width
        
        # Ejecutar detección
        results = self.model(frame, verbose=False, conf=config.CONFIDENCE_THRESHOLD)
        
        detections = []
        
        for result in results:
            boxes = result.boxes
            
            if boxes is None:
                continue
                
            for box in boxes:
                # Obtener coordenadas
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # Calcular centro
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                
                # Calcular área relativa
                box_area = (x2 - x1) * (y2 - y1)
                relative_area = box_area / frame_area
                
                # Obtener clase y confianza
                class_id = int(box.cls[0])
                class_name = self.class_names[class_id]
                confidence = float(box.conf[0])
                
                detection = Detection(
                    class_name=class_name,
                    confidence=confidence,
                    bbox=(int(x1), int(y1), int(x2), int(y2)),
                    center=(int(cx), int(cy)),
                    relative_area=relative_area
                )
                
                detections.append(detection)
        
        return detections
