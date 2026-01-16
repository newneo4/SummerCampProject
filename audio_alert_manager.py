import time
import io
from gtts import gTTS
import config

class AudioAlertManager:
    def __init__(self):
        """Inicializa el gestor de alertas de audio."""
        self.last_alert_time = 0
        self.cooldown = config.ALERT_COOLDOWN  # Segundos entre alertas para evitar saturación
        self.min_danger_threshold = 20
        self.last_message = ""
        # Cache simple para mensajes comunes para reducir llamadas a la API
        self._audio_cache = {}

    def _generate_audio_bytes(self, text: str) -> bytes | None:
        """
        Genera bytes de audio MP3 usando gTTS (Google Text-to-Speech).
        Usa caché en memoria para frases repetidas.
        """
        if text in self._audio_cache:
            return self._audio_cache[text]

        try:
            # lang='es' para español
            tts = gTTS(text=text, lang='es', slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_bytes = fp.getvalue()
            
            # Guardar en caché (límite simple de tamaño podría ser añadido si fuera necesario)
            self._audio_cache[text] = audio_bytes
            return audio_bytes
        except Exception as e:
            print(f"Error generando audio TTS: {e}")
            return None

    def update(self, danger_score: float, context: dict | None = None) -> bytes | None:
        """
        Evalúa si se debe emitir una alerta y devuelve los bytes de audio.

        Args:
            danger_score: Puntuación de peligro (0-100).
            context: Diccionario con información adicional (ej. 'assessments').

        Returns:
            bytes: Audio MP3 si hay alerta, None en caso contrario.
        """
        # 1. Filtro por umbral de peligro
        if danger_score < self.min_danger_threshold:
            return None

        # 2. Control de frecuencia (Cooldown)
        current_time = time.time()
        if current_time - self.last_alert_time < self.cooldown:
            return None

        # 3. Construcción del mensaje
        message = "Peligro detectado."
        
        if context and 'assessments' in context and context['assessments']:
            # Tomar la amenaza principal
            primary_threat = context['assessments'][0]
            
            # Personalizar mensaje según nivel y tipo
            object_name = primary_threat.detection.class_name
            # Traducir o limpiar nombres de clases si es necesario (asumimos que ya vienen bien o son en inglés y gTTS lo leerá como pueda, 
            # pero idealmente deberían estar en español. El código original usa lo que viene de detector/assessment)
            
            # Usar frases cortas y claras
            if primary_threat.danger_level == "ALTO":
                prefix = "¡Peligro alto!"
            elif primary_threat.danger_level == "MEDIO":
                prefix = "Cuidado."
            else:
                prefix = "Atención."
            
            # Construir frase: "Cuidado. Persona al frente."
            # Usamos el mensaje del assessment si es descriptivo, o construimos uno
            if hasattr(primary_threat, 'message') and primary_threat.message:
                 details = primary_threat.message
            else:
                 details = f"{object_name} detectado"

            message = f"{prefix} {details}"

        # Evitar repetir exactamente el mismo mensaje muy seguido si el peligro persiste
        if message == self.last_message and (current_time - self.last_alert_time < self.cooldown * 1.5):
             return None

        # 4. Generar Audio
        audio_bytes = self._generate_audio_bytes(message)
        
        if audio_bytes:
            self.last_alert_time = current_time
            self.last_message = message
            
        return audio_bytes

    def speak_immediate(self, text: str) -> bytes | None:
        """Genera audio inmediato para mensajes del sistema (inicio, parada, etc)."""
        return self._generate_audio_bytes(text)
