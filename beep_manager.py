"""
Módulo para el manejo de alertas sonoras dinámicas (beeps) en Windows.
Utiliza winsound y numpy para generar sonido en memoria con volumen variable.
"""

import winsound
import numpy as np
import time
import struct
import io

class BeepManager:
    def __init__(self):
        """Inicializa el sistema de audio."""
        self.last_beep_time = 0
        self.is_active = True
        self.sample_rate = 22050  # Frecuencia de muestreo estándar
        print("Sistema de audio (Winsound) inicializado.")

    def _generate_wav_bytes(self, frequency=880, duration=0.1, volume=1.0):
        """
        Genera un archivo WAV válido en bytes usando numpy.
        
        Args:
            frequency: Frecuencia en Hz.
            duration: Duración en segundos.
            volume: 0.0 a 1.0.
        """
        # Calcular muestras
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        # Generar onda senoidal
        tone = np.sin(2 * np.pi * frequency * t)
        
        # Aplicar volumen (amplitud)
        # Escalar a 16-bit signed integer (-32767 a 32767)
        audio_data = (tone * volume * 32000).astype(np.int16)
        
        # Crear cabecera WAV
        # Ver formato WAV estándar: RIFF, fmt, data
        
        byte_data = audio_data.tobytes()
        
        # Construir header WAV
        output = io.BytesIO()
        # Riff chunk
        output.write(b'RIFF')
        output.write(struct.pack('<I', 36 + len(byte_data))) # Size
        output.write(b'WAVE')
        # Fmt chunk
        output.write(b'fmt ')
        output.write(struct.pack('<I', 16)) # Subchunk1Size (16 for PCM)
        output.write(struct.pack('<H', 1))  # AudioFormat (1 for PCM)
        output.write(struct.pack('<H', 1))  # NumChannels (1 mono)
        output.write(struct.pack('<I', self.sample_rate)) # SampleRate
        output.write(struct.pack('<I', self.sample_rate * 2)) # ByteRate (SampleRate * NumChannels * BitsPerSample/8)
        output.write(struct.pack('<H', 2))  # BlockAlign (NumChannels * BitsPerSample/8)
        output.write(struct.pack('<H', 16)) # BitsPerSample
        # Data chunk
        output.write(b'data')
        output.write(struct.pack('<I', len(byte_data)))
        output.write(byte_data)
        
        return output.getvalue()

    def update(self, danger_score: float):
        """
        Actualiza el estado del beep basado en el nivel de peligro.
        
        Args:
            danger_score: Puntuación de peligro de 0 a 100.
        """
        if not self.is_active or danger_score < 20: # Umbral mínimo
            return

        current_time = time.time()
        
        # Mapeo de parámetros dinámicos
        # Frecuencia base (pitch): Más agudo si es peligroso
        # 20 score -> 400Hz
        # 100 score -> 1200Hz
        frequency = 400 + (danger_score * 8)
        
        # Volumen: Más fuerte si es peligroso
        # 20 -> 0.2
        # 100 -> 1.0
        volume = max(0.2, (danger_score / 100.0) ** 2)
        
        # Intervalo (Ritmo): Más rápido si es peligroso
        # 20 -> 1.5s
        # 100 -> 0.15s
        interval = max(0.15, 1.5 - (danger_score / 80.0))
        
        # Duración del beep: Corto y seco para alertas rápidas
        duration = 0.1
        if danger_score > 80:
            duration = 0.08 # Más corto y frenético

        if current_time - self.last_beep_time >= interval:
            try:
                wav_data = self._generate_wav_bytes(frequency, duration, volume)
                # SND_ASYNC | SND_MEMORY | SND_NODEFAULT
                # ASYNC: No bloquea
                # MEMORY: Toca bytes
                # NODEFAULT: No toca sonido error si falla
                winsound.PlaySound(wav_data, winsound.SND_ASYNC | winsound.SND_MEMORY | winsound.SND_NODEFAULT)
                self.last_beep_time = current_time
            except Exception as e:
                print(f"Error reproduciendo beep: {e}")
                self.is_active = False # Desactivar si falla para no saturar consola

    def stop(self):
        """Detiene cualquier sonido."""
        if self.is_active:
            # Purge sounds
            winsound.PlaySound(None, winsound.SND_PURGE)
