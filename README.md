# 👁️ Asistente Visual - Detección de Objetos para Personas Ciegas

Aplicación de detección de objetos en tiempo real usando YOLOv8 + Gemini AI, diseñada para asistir a personas con discapacidad visual mediante alertas de voz.

## 🚀 Características

- **Detección en tiempo real**: Usa YOLOv8 para detectar objetos en la webcam
- **Alertas de voz**: Notifica con síntesis de voz cuando hay objetos cercanos
- **Niveles de peligro**: Evalúa el riesgo basado en tipo de objeto, tamaño y posición
- **Gemini AI**: Análisis inteligente de escena con descripciones contextuales
- **Interfaz accesible**: Botones grandes y alto contraste

## ✨ Funciones Gemini AI

- **Describir Escena**: Descripción detallada de lo que hay alrededor
- **Consejos de Navegación**: Sugerencias inteligentes sobre hacia dónde moverse
- **Preguntas**: Responde preguntas sobre la escena ("¿Hay una puerta cerca?")
- **Alertas Contextuales**: Avisos inteligentes sobre peligros

## 📦 Instalación

```bash
pip install -r requirements.txt
```

## ▶️ Uso

```bash
streamlit run app.py
```

### Configurar Gemini (Opcional pero recomendado)

1. Ve a [Google AI Studio](https://aistudio.google.com/apikey)
2. Crea una API Key gratuita
3. Pégala en la app en el campo "API Key de Google AI"

## ⚠️ Niveles de Peligro

| Nivel | Color | Descripción |
|-------|-------|-------------|
| ALTO | 🔴 Rojo | Objeto muy cerca, peligro inmediato |
| MEDIO | 🟠 Naranja | Objeto a distancia media, precaución |
| BAJO | 🟢 Verde | Objeto detectado pero a distancia segura |

## 🔧 Configuración

Modifica `config.py` para ajustar:
- Umbrales de peligro
- Velocidad de voz
- Cooldown entre alertas

