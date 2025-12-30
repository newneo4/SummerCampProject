"""
Sistema de alertas de voz para personas ciegas.
"""

import pyttsx3
import threading
import time
from queue import PriorityQueue
from dataclasses import dataclass, field
from typing import Dict
import config


@dataclass(order=True)
class VoiceMessage:
    """Mensaje de voz con prioridad."""
    priority: int
    message: str = field(compare=False)
    object_type: str = field(compare=False)


class VoiceAlert:
    """Sistema de alertas de voz con cola de prioridad y cooldown."""
    
    def __init__(self):
        """Inicializa el motor de voz."""
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', config.VOICE_RATE)
        self.engine.setProperty('volume', config.VOICE_VOLUME)
        
        # Intentar configurar voz en español
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        # Cola de mensajes con prioridad
        self.message_queue: PriorityQueue = PriorityQueue()
        
        # Registro de último tiempo de alerta por tipo de objeto
        self.last_alert_time: Dict[str, float] = {}
        
        # Control de threading
        self.is_running = False
        self.thread = None
        self._lock = threading.Lock()
        
    def start(self):
        """Inicia el hilo de procesamiento de voz."""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._process_queue, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Detiene el sistema de voz."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
    
    def alert(self, message: str, object_type: str, danger_level: str):
        """
        Agrega una alerta a la cola si no está en cooldown.
        
        Args:
            message: Mensaje a pronunciar
            object_type: Tipo de objeto (para cooldown)
            danger_level: Nivel de peligro (ALTO, MEDIO, BAJO)
        """
        current_time = time.time()
        
        # Verificar cooldown
        with self._lock:
            last_time = self.last_alert_time.get(object_type, 0)
            if current_time - last_time < config.ALERT_COOLDOWN:
                return  # Aún en cooldown
            
            self.last_alert_time[object_type] = current_time
        
        # Asignar prioridad (menor número = mayor prioridad)
        priority_map = {"ALTO": 0, "MEDIO": 1, "BAJO": 2}
        priority = priority_map.get(danger_level, 2)
        
        # Agregar a la cola
        voice_message = VoiceMessage(
            priority=priority,
            message=message,
            object_type=object_type
        )
        self.message_queue.put(voice_message)
    
    def _process_queue(self):
        """Procesa la cola de mensajes de voz."""
        while self.is_running:
            try:
                # Obtener mensaje con timeout para poder verificar is_running
                if not self.message_queue.empty():
                    voice_message = self.message_queue.get(timeout=0.5)
                    self._speak(voice_message.message)
                else:
                    time.sleep(0.1)
            except Exception:
                pass
    
    def _speak(self, message: str):
        """Pronuncia un mensaje."""
        try:
            self.engine.say(message)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error en síntesis de voz: {e}")
    
    def speak_immediate(self, message: str):
        """Pronuncia un mensaje inmediatamente (para mensajes de sistema)."""
        try:
            self.engine.say(message)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error en síntesis de voz: {e}")
