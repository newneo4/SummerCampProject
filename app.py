"""
Aplicación de Detección de Objetos para Personas Ciegas
Utiliza YOLOv8 + Gemini AI para detectar objetos y alertar con voz.
Adaptado para trabajar con imágenes estáticas desde el navegador.
"""

import streamlit as st
import cv2
import numpy as np
from detector import ObjectDetector
from danger_assessment import DangerAssessor
from gemini_assistant import GeminiAssistant
from audio_alert_manager import AudioAlertManager
import config
import time
from PIL import Image

# Configuración de página
st.set_page_config(
    page_title="Asistente Visual - Detección de Objetos",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para accesibilidad
st.markdown("""
<style>
    /* Fuentes grandes y alto contraste */
    .main {
        background-color: #1a1a2e;
        color: #ffffff;
    }
    
    .stButton > button {
        width: 100%;
        height: 60px;
        font-size: 20px !important;
        font-weight: bold;
        border-radius: 12px;
        margin: 8px 0;
    }
    
    .gemini-btn > button {
        background-color: #4285f4;
        color: white;
        border: 4px solid #8ab4f8;
        height: 80px;
        font-size: 22px !important;
    }
    
    .gemini-btn > button:hover {
        background-color: #8ab4f8;
    }
    
    /* Indicadores de peligro */
    .danger-high {
        background-color: #dc3545;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        animation: pulse 0.5s infinite;
        margin: 15px 0;
    }
    
    .danger-medium {
        background-color: #fd7e14;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 15px 0;
    }
    
    .danger-low {
        background-color: #28a745;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 15px 0;
    }
    
    .danger-none {
        background-color: #6c757d;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 15px 0;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .title {
        text-align: center;
        font-size: 38px;
        font-weight: bold;
        color: #ffffff;
        padding: 15px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 20px;
    }
    
    .gemini-box {
        background: linear-gradient(135deg, #1a73e8 0%, #4285f4 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        font-size: 24px;
        font-weight: 500;
        margin-top: 20px;
    }
    
    /* Ocultar elementos de Streamlit que distraen */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_detector():
    """Carga y cachea el modelo YOLO."""
    return ObjectDetector()

@st.cache_resource
def load_assessor():
    """Carga y cachea el evaluador de peligro."""
    return DangerAssessor()

@st.cache_resource
def get_audio_manager():
    """Obtiene el gestor de audio."""
    return AudioAlertManager()

def init_session_state():
    """Inicializa el estado de la sesión."""
    if 'last_processed_time' not in st.session_state:
        st.session_state.last_processed_time = 0
    
    if 'current_danger' not in st.session_state:
        st.session_state.current_danger = "NINGUNO"
        
    if 'gemini' not in st.session_state:
        try:
            st.session_state.gemini = GeminiAssistant(config.GEMINI_API_KEY)
            st.session_state.gemini_enabled = True
        except Exception as e:
            # st.error(f"Error al conectar con Gemini: {e}") 
            # Silent fail to avoid clustering UI if API key is missing
            st.session_state.gemini_enabled = False
            
    if 'last_gemini_description' not in st.session_state:
        st.session_state.last_gemini_description = None
        
    if 'current_frame_bgr' not in st.session_state:
        st.session_state.current_frame_bgr = None

def process_uploaded_image(uploaded_file):
    """
    Convierte el archivo subido a una imagen OpenCV (BGR).
    """
    if uploaded_file is None:
        return None
    
    # Leer archivo como bytes
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    
    # Decodificar con OpenCV (carga en BGR por defecto)
    image_bgr = cv2.imdecode(file_bytes, 1)
    
    return image_bgr

def draw_detections(frame, assessments):
    """Dibuja las detecciones en el frame."""
    if frame is None:
        return None
        
    draw_frame = frame.copy()
    
    for assessment in assessments:
        det = assessment.detection
        color = config.DANGER_COLORS.get(assessment.danger_level, (255, 255, 255))
        
        cv2.rectangle(draw_frame, 
                     (det.bbox[0], det.bbox[1]), 
                     (det.bbox[2], det.bbox[3]), 
                     color, 3)
        
        label = f"{assessment.danger_level}: {det.class_name}"
        
        # Fondo para el texto para mayor legibilidad
        (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        cv2.rectangle(draw_frame, 
                     (det.bbox[0], det.bbox[1] - text_h - 10), 
                     (det.bbox[0] + text_w, det.bbox[1]), 
                     color, -1)
                     
        cv2.putText(draw_frame, label,
                   (det.bbox[0], det.bbox[1] - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    return draw_frame

def update_danger_ui(placeholder, danger_level):
    """Actualiza el indicador visual de peligro."""
    with placeholder.container():
        if danger_level == "ALTO":
            st.markdown('<div class="danger-high">🔴 PELIGRO ALTO</div>', unsafe_allow_html=True)
        elif danger_level == "MEDIO":
            st.markdown('<div class="danger-medium">🟠 PRECAUCIÓN</div>', unsafe_allow_html=True)
        elif danger_level == "BAJO":
            st.markdown('<div class="danger-low">🟢 SEGURO</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="danger-none">⚪ SIN DETECCIONES</div>', unsafe_allow_html=True)

def main():
    """Función principal de la aplicación."""
    init_session_state()
    
    # Cargar recursos (cacheados)
    with st.spinner("Cargando sistema de visión..."):
        detector = load_detector()
        assessor = load_assessor()
        audio_manager = get_audio_manager()

    st.markdown('<div class="title">👁️ ASISTENTE VISUAL</div>', unsafe_allow_html=True)
    
    # Layout Principal
    col_cam, col_info = st.columns([2, 1])
    
    # --- Columna de Información / Estado ---
    with col_info:
        st.markdown("### 🔊 Estado")
        
        # Placeholder para indicador de peligro
        danger_placeholder = st.empty()
        update_danger_ui(danger_placeholder, st.session_state.current_danger)
        
        # Placeholder para audio (importante: debe estar presente para reproducir)
        audio_placeholder = st.empty()
        
        st.markdown("### 🤖 Asistente")
        if st.session_state.gemini_enabled:
            st.markdown('<div class="gemini-btn">', unsafe_allow_html=True)
            if st.button("🎤 DESCRIBIR ESCENA", key="describe_btn", disabled=(st.session_state.current_frame_bgr is None)):
                if st.session_state.current_frame_bgr is not None:
                    with st.spinner("Analizando con IA..."):
                        try:
                            # Re-detectar para asegurar frescura o usar lógica existente
                            detections = detector.detect(st.session_state.current_frame_bgr)
                            
                            if not detections:
                                description_text = "No veo objetos definidos, pero describiré lo que veo en general."
                                # Aquí podríamos pasar la imagen completa a Gemini si el asistente lo soportara (multimodal)
                                # Por ahora usamos el resumen de objetos o 'nada'
                            else:
                                det_strs = [f"{d.class_name}" for d in detections]
                                summary = ", ".join(det_strs) if det_strs else "una escena vacía"
                                
                                description_text = st.session_state.gemini.get_quick_description(summary)
                            
                            st.session_state.last_gemini_description = description_text
                            
                            # Reproducir descripción
                            audio_bytes = audio_manager.speak_immediate(description_text)
                            if audio_bytes:
                                audio_placeholder.audio(audio_bytes, format="audio/mp3", autoplay=True)
                                
                        except Exception as e:
                            st.error(f"Error Gemini: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.session_state.last_gemini_description:
                 st.markdown(f'<div class="gemini-box">{st.session_state.last_gemini_description}</div>', unsafe_allow_html=True)

    # --- Columna de Cámara y Visión ---
    with col_cam:
        # Input de cámara nativo de Streamlit
        img_file = st.camera_input("Capturar Entorno", label_visibility="visible")
        
        if img_file is not None:
            # Procesar imagen solo si ha cambiado o es nueva carga
            # st.camera_input devuelve un objeto nuevo en cada captura
            
            # 1. Convertir imagen
            frame_bgr = process_uploaded_image(img_file)
            st.session_state.current_frame_bgr = frame_bgr # Guardar para uso de Gemini
            
            if frame_bgr is not None:
                # 2. Detectar
                detections = detector.detect(frame_bgr)
                
                # 3. Evaluar Peligro
                assessments = []
                frame_width = frame_bgr.shape[1]
                
                for det in detections:
                    assessment = assessor.assess(det, frame_width)
                    if assessment:
                        assessments.append(assessment)
                
                # Ordenar por peligro
                assessments.sort(key=lambda x: x.danger_score, reverse=True)
                
                # 4. Actualizar Estado Global
                if assessments:
                    st.session_state.current_danger = assessments[0].danger_level
                    max_danger_score = assessments[0].danger_score
                    
                    # Generar alerta de audio automática
                    # Nota: update() gestiona el cooldown internamente
                    audio_bytes = audio_manager.update(max_danger_score, {'assessments': assessments})
                    if audio_bytes:
                         audio_placeholder.audio(audio_bytes, format="audio/mp3", autoplay=True)
                else:
                    st.session_state.current_danger = "NINGUNO"
                    update_danger_ui(danger_placeholder, "NINGUNO")
                    # Intentar mensaje de "Todo despejado" si veníamos de peligro? (Opcional, puede saturar)
                
                # Actualizar UI de peligro tras el cálculo
                update_danger_ui(danger_placeholder, st.session_state.current_danger)
                
                # 5. Dibujar Visualización
                final_frame = draw_detections(frame_bgr, assessments)
                
                # Convertir a RGB para mostrar en Streamlit
                final_frame_rgb = cv2.cvtColor(final_frame, cv2.COLOR_BGR2RGB)
                
                st.image(final_frame_rgb, caption="Análisis de entorno", use_container_width=True)
                
        else:
            # Estado inactivo / esperando cámara
            st.info("📷 Esperando captura de imagen...")
            st.markdown("""
            <div style="text-align: center; color: #666;">
                Toma una foto para analizar tu entorno.
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
