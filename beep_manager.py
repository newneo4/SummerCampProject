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
        self.sample_rate = 22050 
        print("Sistema de audio (Winsound) inicializado.")

    def _generate_wav_bytes(self, frequency=880, duration=0.1, volume=1.0):
        """
        Genera un archivo WAV válido en bytes usando numpy.
        
        Args:
            frequency: Frecuencia en Hz.
            duration: Duración en segundos.
            volume: 0.0 a 1.0.
        """
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        tone = np.sin(2 * np.pi * frequency * t)
        
        audio_data = (tone * volume * 32000).astype(np.int16)
                
        byte_data = audio_data.tobytes()
        
        output = io.BytesIO()
        output.write(b'RIFF')
        output.write(struct.pack('<I', 36 + len(byte_data))) 
        output.write(b'WAVE')
        output.write(b'fmt ')
        output.write(struct.pack('<I', 16))  
        output.write(struct.pack('<H', 1))  
        output.write(struct.pack('<H', 1))  
        output.write(struct.pack('<I', self.sample_rate)) 
        output.write(struct.pack('<I', self.sample_rate * 2)) 
        output.write(struct.pack('<H', 2)) 
        output.write(struct.pack('<H', 16)) 
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
        if not self.is_active or danger_score < 20: 
            return

        current_time = time.time()
        
        frequency = 400 + (danger_score * 8)
        
        volume = max(0.2, (danger_score / 100.0) ** 2)
        
        interval = max(0.15, 1.5 - (danger_score / 80.0))
        
        duration = 0.1
        if danger_score > 80:
            duration = 0.08 

        if current_time - self.last_beep_time >= interval:
            try:
                wav_data = self._generate_wav_bytes(frequency, duration, volume)
                winsound.PlaySound(wav_data, winsound.SND_ASYNC | winsound.SND_MEMORY | winsound.SND_NODEFAULT)
                self.last_beep_time = current_time
            except Exception as e:
                print(f"Error reproduciendo beep: {e}")
                self.is_active = False 

    def stop(self):
        """Detiene cualquier sonido."""
        if self.is_active:
            winsound.PlaySound(None, winsound.SND_PURGE)
