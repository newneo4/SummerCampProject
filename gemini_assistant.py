"""
Módulo de integración con Gemini AI para descripciones de escena y consejos de navegación.
"""

import google.generativeai as genai
from PIL import Image
import numpy as np
import io
import time
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class SceneDescription:
    """Descripción de la escena por Gemini."""
    summary: str
    navigation_advice: str
    potential_hazards: List[str]
    safe_direction: str


class GeminiAssistant:
    """Asistente de IA usando Gemini para análisis de escena (Modo Texto)."""
    
    def __init__(self, api_key: str):
        """
        Inicializa el asistente Gemini.
        
        Args:
            api_key: API key de Google AI Studio
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-flash-latest')
        print("Gemini Assistant iniciado con modelo: gemini-flash-latest")
        self.last_analysis_time = 0
        self.analysis_cooldown = 5.0  
        self.last_description: Optional[SceneDescription] = None
        
    def analyze_scene(self, detections_info: str) -> Optional[SceneDescription]:
        """
        Analiza la escena usando solo info de detecciones (Text-Only).
        
        Args:
            detections_info: Información de detecciones YOLO
            
        Returns:
            Descripción de la escena o None si en cooldown
        """
        current_time = time.time()
        
        if current_time - self.last_analysis_time < self.analysis_cooldown:
            return self.last_description
        
        self.last_analysis_time = current_time
        
        try:
            prompt = f"""Eres un asistente visual para una persona ciega.
Tienes acceso a una lista de objetos detectados por sensores.

OBJETOS DETECTADOS: {detections_info}

Responde en español de forma MUY BREVE y CLARA:

1. RESUMEN: Frase corta de lo que hay.
2. CONSEJO DE NAVEGACIÓN: Basado en los peligros detectados.
3. PELIGROS: Lista de amenazas (si las hay).
4. DIRECCIÓN SEGURA: Dónde moverse.

Sé conciso."""

            response = self.model.generate_content(prompt)
            
            text = response.text
            description = self._parse_response(text)
            self.last_description = description
            
            return description
            
        except Exception as e:
            print(f"ERROR DETALLADO GEMINI (Analyze Scene): {e}")
            return SceneDescription(
                summary=f"Error en IA: {str(e)[:50]}...",
                navigation_advice="Error técnico",
                potential_hazards=[],
                safe_direction="detenerse"
            )
    
    def _parse_response(self, text: str) -> SceneDescription:
        """Parsea la respuesta de Gemini."""
        lines = text.strip().split('\n')
        
        summary = ""
        navigation = ""
        hazards = []
        safe_dir = "detenerse"
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            lower_line = line.lower()
            
            if 'resumen' in lower_line or '1.' in line:
                current_section = 'summary'
                if ':' in line:
                    summary = line.split(':', 1)[1].strip()
            elif 'consejo' in lower_line or 'navegación' in lower_line or '2.' in line:
                current_section = 'navigation'
                if ':' in line:
                    navigation = line.split(':', 1)[1].strip()
            elif 'peligro' in lower_line or '3.' in line:
                current_section = 'hazards'
                if ':' in line:
                    hazard_text = line.split(':', 1)[1].strip()
                    hazards = [h.strip() for h in hazard_text.split(',') if h.strip()]
            elif 'dirección' in lower_line or 'segura' in lower_line or '4.' in line:
                current_section = 'safe_dir'
                if ':' in line:
                    safe_dir = line.split(':', 1)[1].strip()
            else:
                if current_section == 'summary' and not summary:
                    summary = line
                elif current_section == 'navigation' and not navigation:
                    navigation = line
                elif current_section == 'hazards' and not hazards:
                    hazards = [h.strip() for h in line.split(',') if h.strip()]
                elif current_section == 'safe_dir' and safe_dir == "detenerse":
                    safe_dir = line
        
        if not summary:
            summary = "Procesando entorno..."
        if not navigation:
            navigation = "Precaución"
        
        return SceneDescription(
            summary=summary,
            navigation_advice=navigation,
            potential_hazards=hazards,
            safe_direction=safe_dir
        )
    
    def answer_question(self, detections_info: str, question: str) -> str:
        """
        Responde una pregunta basada en las detecciones.
        """
        try:
            prompt = f"""Eres un asistente para una persona ciega.
OBJETOS DETECTADOS: {detections_info}

PREGUNTA USUARIO: "{question}"

Responde basándote SOLO en los objetos detectados. Si no sabes, dilo.
Sé breve."""

            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_quick_description(self, detections_info: str) -> str:
        """
        Descripción rápida para voz basada en detecciones.
        """
        try:
            prompt = f"""Resume en 1 oración qué hay alrededor para un ciego.
OBJETOS: {detections_info}
Idioma: Español."""

            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"ERROR DETALLADO GEMINI: {e}")
            return f"Error técnico: {str(e)}"
