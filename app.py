"""
Aplicación de Detección de Objetos para Personas Ciegas
Utiliza YOLOv8 + Gemini AI para detectar objetos y alertar con voz.
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
        height: 100px;
        font-size: 28px !important;
        font-weight: bold;
        border-radius: 20px;
        margin: 8px 0;
    }
    
    .start-btn > button {
        background-color: #00a86b;
        color: white;
        border: 4px solid #00ff9d;
    }
    
    .start-btn > button:hover {
        background-color: #00ff9d;
        color: #1a1a2e;
    }
    
    .stop-btn > button {
        background-color: #dc3545;
        color: white;
        border: 4px solid #ff6b6b;
    }
    
    .stop-btn > button:hover {
        background-color: #ff6b6b;
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
    
    .status-text {
        font-size: 20px;
        text-align: center;
        padding: 10px;
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
    
    .gemini-title {
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_available_cameras():
    """Detecta las cámaras disponibles en el sistema."""
    available_cameras = {}
    # Probar los primeros 10 índices
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available_cameras[f"Cámara {i}"] = i
            cap.release()
    return available_cameras


def init_session_state():
    """Inicializa el estado de la sesión."""
    if 'is_running' not in st.session_state:
        st.session_state.is_running = False
    if 'camera_index' not in st.session_state:
        st.session_state.camera_index = 0
    if 'detector' not in st.session_state:
        st.session_state.detector = None
    if 'assessor' not in st.session_state:
        st.session_state.assessor = DangerAssessor()
    if 'audio_manager' not in st.session_state:
        st.session_state.audio_manager = AudioAlertManager()
    if 'pending_audio' not in st.session_state:
        st.session_state.pending_audio = None
    if 'current_danger' not in st.session_state:
        st.session_state.current_danger = "NINGUNO"
    if 'gemini' not in st.session_state:
        try:
            st.session_state.gemini = GeminiAssistant(config.GEMINI_API_KEY)
            st.session_state.gemini_enabled = True
        except Exception as e:
            st.error(f"Error al conectar con Gemini: {e}")
            st.session_state.gemini_enabled = False
            
    if 'last_gemini_description' not in st.session_state:
        st.session_state.last_gemini_description = None
    if 'current_frame' not in st.session_state:
        st.session_state.current_frame = None


def draw_detections(frame, assessments):
    """Dibuja las detecciones en el frame."""
    for assessment in assessments:
        det = assessment.detection
        color = config.DANGER_COLORS.get(assessment.danger_level, (255, 255, 255))
        
        cv2.rectangle(frame, 
                     (det.bbox[0], det.bbox[1]), 
                     (det.bbox[2], det.bbox[3]), 
                     color, 3)
        
        label = f"{assessment.danger_level}: {det.class_name}"
        cv2.putText(frame, label,
                   (det.bbox[0], det.bbox[1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    
    return frame


def get_detections_summary(assessments) -> str:
    """Genera un resumen de las detecciones para Gemini."""
    if not assessments:
        return ""
    
    summary_parts = []
    for a in assessments[:8]:
        summary_parts.append(f"{a.detection.class_name}")
    
    return ", ".join(summary_parts)



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
    
    # Reproducir audio pendiente si existe
    if st.session_state.pending_audio:
        st.audio(st.session_state.pending_audio, format="audio/mp3", autoplay=True)
        st.session_state.pending_audio = None

    st.markdown('<div class="title">👁️ ASISTENTE VISUAL CON IA</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### 🎛️ Controles")
        
        if not st.session_state.is_running:
            cameras = get_available_cameras()
            if cameras:
                camera_options = list(cameras.keys())
                selected_cam_name = st.selectbox(
                    "📷 Seleccionar Cámara", 
                    options=camera_options,
                    index=0
                )
                st.session_state.camera_index = cameras[selected_cam_name]
            else:
                st.error("No se detectaron cámaras.")
        
        if not st.session_state.is_running:
            st.markdown('<div class="start-btn">', unsafe_allow_html=True)
            if st.button("▶️ INICIAR", key="start"):
                st.session_state.is_running = True
                if st.session_state.detector is None:
                    with st.spinner("Cargando modelo YOLO..."):
                        st.session_state.detector = ObjectDetector()
                st.session_state.pending_audio = st.session_state.audio_manager.speak_immediate("Sistema iniciado.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
            if st.button("⏹️ DETENER", key="stop"):
                st.session_state.is_running = False
                st.session_state.pending_audio = st.session_state.audio_manager.speak_immediate("Sistema detenido.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### ⚠️ Nivel de Peligro")
        danger_placeholder = st.empty()
        update_danger_ui(danger_placeholder, st.session_state.current_danger)
            
        st.markdown("### 🤖 Asistente IA")
        if st.session_state.gemini_enabled and st.session_state.is_running:
            st.markdown('<div class="gemini-btn">', unsafe_allow_html=True)
            if st.button("🎤 DESCRIBIR ESCENA", key="describe_manual"):
                 if st.session_state.detector and st.session_state.current_frame is not None:
                    with st.spinner("Analizando..."):
                        try:
                            temp_dets = st.session_state.detector.detect(st.session_state.current_frame)
                            
                            if not temp_dets:
                                description_text = "No detecto obstáculos visibles al frente."
                            else:
                                det_strs = [f"{d.class_name}" for d in temp_dets]
                                summary = ", ".join(det_strs)
                                
                                description_text = st.session_state.gemini.get_quick_description(summary)
                            
                            st.session_state.last_gemini_description = description_text
                            audio_data = st.session_state.audio_manager.speak_immediate(description_text)
                            if audio_data:
                                st.audio(audio_data, format="audio/mp3", autoplay=True)
                            
                        except Exception as e:
                            st.error(f"Error Gemini: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
        
    with col1:
        video_placeholder = st.empty()
        
        if st.session_state.last_gemini_description:
            st.markdown(f"""
            <div class="gemini-box">
                {st.session_state.last_gemini_description}
            </div>
            """, unsafe_allow_html=True)
        
        if st.session_state.is_running:
            cap = cv2.VideoCapture(st.session_state.get('camera_index', 0))
            
            if not cap.isOpened():
                st.error(f"❌ No se pudo acceder a la cámara {st.session_state.get('camera_index', 0)}. Verifica que esté conectada.")
                st.session_state.is_running = False
            else:
                while st.session_state.is_running:
                    ret, frame = cap.read()
                    
                    if not ret:
                        st.warning("⚠️ Error al leer frame de la cámara")
                        break
                    
                    st.session_state.current_frame = frame.copy()
                    
                    detections = st.session_state.detector.detect(frame)
                    
                    assessments = []
                    frame_width = frame.shape[1]
                    
                    for det in detections:
                        assessment = st.session_state.assessor.assess(det, frame_width)
                        if assessment:
                            assessments.append(assessment)
                    
                    assessments.sort(key=lambda x: x.danger_score, reverse=True)
                    
                    # Placeholder para audio alertas
                    if 'audio_status' not in st.session_state:
                         st.session_state.audio_status = st.empty()
                    
                    if assessments:
                        st.session_state.current_danger = assessments[0].danger_level
                        max_danger_score = assessments[0].danger_score
                        
                        update_danger_ui(danger_placeholder, st.session_state.current_danger)
                        
                        audio_bytes = st.session_state.audio_manager.update(max_danger_score, {'assessments': assessments})
                        if audio_bytes:
                             st.session_state.audio_status.audio(audio_bytes, format="audio/mp3", autoplay=True)

                    else:
                        st.session_state.current_danger = "NINGUNO"
                        update_danger_ui(danger_placeholder, "NINGUNO")
                        

                    
                    frame = draw_detections(frame, assessments)
                    
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
                    
                    time.sleep(0.01) 
                
                cap.release()
        else:
            st.info("👆 Presiona **INICIAR** para comenzar la detección")
            st.markdown("""
            <div style="text-align: center; padding: 50px; opacity: 0.5;">
                <h1>📷</h1>
                <p>Cámara inactiva</p>
            </div>
            """, unsafe_allow_html=True)



if __name__ == "__main__":
    main()
