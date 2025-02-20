import sys
import threading
import datetime
import os
import json
import speech_recognition as sr
import pyttsx3
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QCheckBox, QSlider
from PyQt6.QtCore import Qt

# Configuración de la voz
def configurar_voz():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if "spanish" in voice.name.lower() or "es" in voice.id:
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', 145)
    return engine

# Hablar con voz
def hablar(engine, texto):
    def run():
        engine.say(texto)
        engine.runAndWait()
    threading.Thread(target=run, daemon=True).start()

# Escuchar al usuario
def escuchar():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Escuchando...")
        try:
            audio = recognizer.listen(source, timeout=5)  # Tiempo de espera máximo
            texto = recognizer.recognize_google(audio, language="es-ES").lower()
            print("Entendí:", texto)
            return texto
        except sr.UnknownValueError:
            print("No entendí el audio.")
            return "No entendí"
        except sr.RequestError:
            print("Error con el servicio de reconocimiento.")
            return "Error de conexión"
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")
            return "Error desconocido"

# Prompts para conversación continua
def obtener_prompt_por_hora():
    hora_actual = datetime.datetime.now().hour
    if 6 <= hora_actual < 12:
        return "¡Buenos días! 😊"
    elif 12 <= hora_actual < 18:
        return "¡Buenas tardes! 🌞"
    else:
        return "¡Buenas noches! 🌙"

PROMPTS_CONVERSACION = {
    "saludo": [
        "hola", "buenos días", "buenas tardes", "buenas noches",
        "qué tal", "cómo estás", "hola, ¿cómo va todo?"
    ],
    "preguntas_iniciales": [
        "¿Cómo estás hoy?",
        "¿Qué tal tu día hasta ahora?",
        "¿En qué puedo ayudarte hoy?",
        "¿Hay algo en lo que quieras pensar juntos?"
    ],
    "respuestas_emocionales": {
        "triste": [
            "Lamento escuchar eso. ¿Quieres contarme más sobre lo que te está afectando?",
            "Es válido sentir tristeza. ¿Qué crees que podría ayudarte a sentirte mejor?"
        ],
        "feliz": [
            "¡Me alegra mucho escuchar eso! ¿Hay algo en particular que te haya hecho sentir así?",
            "La felicidad es maravillosa. ¿Qué has disfrutado hoy?"
        ],
        "ansioso": [
            "Entiendo que la ansiedad puede ser abrumadora. ¿Qué crees que está causando esa sensación?",
            "Respira profundamente. ¿Qué piensas que podrías hacer para calmarte?"
        ],
        "enojado": [
            "El enojo es una emoción natural. ¿Qué crees que te está haciendo sentir así?",
            "A veces, el enojo nos dice algo importante. ¿Quieres hablar más sobre eso?"
        ],
        "neutral": [
            "Gracias por compartir cómo te sientes. ¿Hay algo más en lo que pueda ayudarte?",
            "Estoy aquí para escucharte. ¿Qué más te gustaría decir?"
        ]
    },
    "preguntas_seguimiento": [
        "¿Qué más te gustaría compartir?",
        "¿Cómo te sientes acerca de eso?",
        "¿Qué crees que podrías hacer al respecto?",
        "¿Te gustaría hablar de algo más?"
    ],
    "despedida": [
        "Gracias por compartir tus pensamientos conmigo. Cuídate mucho.",
        "Siempre estaré aquí cuando me necesites. Hasta luego.",
        "Que tengas un día lleno de paz y bienestar."
    ]
}

# Historial emocional del usuario
def guardar_estado_emocional(usuario, emocion, archivo="estado_emocional.json"):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    
    data[usuario] = emocion
    
    with open(archivo, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def cargar_estado_emocional(usuario, archivo="estado_emocional.json"):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                return data.get(usuario, "neutral")
            except json.JSONDecodeError:
                return "neutral"
    return "neutral"

# Guardar perfil del usuario
def guardar_perfil_usuario(usuario, datos, archivo="perfil_usuario.json"):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    
    data[usuario] = datos
    
    with open(archivo, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Cargar perfil del usuario
def cargar_perfil_usuario(usuario, archivo="perfil_usuario.json"):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                return data.get(usuario, {})
            except json.JSONDecodeError:
                return {}
    return {}

# Datos iniciales del usuario
PERFIL_USUARIO = {
    "nombre": "Usuario",
    "edad": 22,
    "ocupaciones": ["programación", "cocinero"],
    "proyectos": ["Construyendo un asistente virtual"],
    "horarios": {
        "estudio": ["mañana", "siesta"],
        "trabajo": ["medio día", "noche"]
    }
}

# Guardar el perfil al iniciar
guardar_perfil_usuario("usuario", PERFIL_USUARIO)

# Recursos útiles para el proyecto
RECURSOS_PROYECTO = {
    "reconocimiento_voz": [
        "Usa la biblioteca SpeechRecognition para capturar audio.",
        "Explora Google Cloud Speech-to-Text para un reconocimiento más avanzado."
    ],
    "procesamiento_lenguaje": [
        "Dialogflow es una excelente herramienta para NLP.",
        "Rasa es una alternativa open-source para crear chatbots avanzados."
    ],
    "diseño_interfaz": [
        "PyQt6 es genial para interfaces gráficas.",
        "Prueba Tkinter si prefieres algo más ligero."
    ],
    "aprendizaje_automatico": [
        "TensorFlow y PyTorch son frameworks populares para entrenar modelos.",
        "Keras es una opción más simple para principiantes."
    ]
}

# Generar respuesta continua
def generar_respuesta_continua(comando, usuario="usuario"):
    perfil = cargar_perfil_usuario(usuario)
    estado_actual = cargar_estado_emocional(usuario)
    hora_actual = datetime.datetime.now().hour

    # Saludos generales
    for saludo in PROMPTS_CONVERSACION["saludo"]:
        if saludo in comando:
            return f"{obtener_prompt_por_hora()} {PROMPTS_CONVERSACION['preguntas_iniciales'][0]}"

    # Detectar emociones específicas
    emociones = {
        "triste": ["triste", "deprimido", "mal", "infeliz"],
        "feliz": ["feliz", "contento", "alegre", "bien"],
        "ansioso": ["ansioso", "preocupado", "nervioso", "estresado"],
        "enojado": ["enojado", "furioso", "irritado", "molesto"]
    }

    for emocion, palabras_clave in emociones.items():
        if any(palabra in comando for palabra in palabras_clave):
            guardar_estado_emocional(usuario, emocion)
            respuesta = PROMPTS_CONVERSACION["respuestas_emocionales"][emocion][0]
            pregunta_seguimiento = PROMPTS_CONVERSACION["preguntas_seguimiento"][0]
            return f"{respuesta} {pregunta_seguimiento}"

    # Preguntas basadas en el perfil del usuario
    if "estudiar" in comando or "programación" in comando:
        if 6 <= hora_actual < 12 or 12 <= hora_actual < 15:
            return "¡Qué bien que estás estudiando programación! ¿En qué proyecto estás trabajando hoy?"
        else:
            return "¿Cómo te fue estudiando programación hoy? ¿Lograste avanzar en algo interesante?"

    if "trabajar" in comando or "cocinero" in comando:
        if 12 <= hora_actual < 18:
            return "Espero que tengas un buen día en el trabajo como cocinero. ¿Qué vas a preparar hoy?"
        elif 18 <= hora_actual < 24:
            return "El turno de la noche puede ser agotador. ¿Cómo te sientes después del trabajo?"

    if "descansar" in comando or "siesta" in comando:
        if 12 <= hora_actual < 15:
            return "La siesta es importante para recargar energías. ¿Te sientes más relajado después de descansar?"

    # Preguntas sobre el proyecto del asistente virtual
    if "asistente virtual" in comando or "proyecto" in comando:
        return (
            "¡Qué emocionante que estás construyendo un asistente virtual! Aquí tienes algunos consejos: "
            "1. Usa APIs como Dialogflow o Rasa para mejorar el procesamiento del lenguaje natural. "
            "2. Modulariza tu código para facilitar futuras mejoras. "
            "3. Prueba tu asistente con diferentes usuarios para obtener feedback. ¿En qué parte del proyecto necesitas ayuda?"
        )

    if "reconocimiento de voz" in comando:
        return f"Aquí tienes algunos consejos sobre reconocimiento de voz: {', '.join(RECURSOS_PROYECTO['reconocimiento_voz'])}. ¿Algo más en lo que pueda ayudarte?"

    # Despedida
    if "adiós" in comando or "hasta luego" in comando:
        return PROMPTS_CONVERSACION["despedida"][0]

    # Respuesta neutral si no hay coincidencias
    pregunta_seguimiento = PROMPTS_CONVERSACION["preguntas_seguimiento"][0]
    return f"Gracias por compartir. {pregunta_seguimiento}"

# Persistencia de datos con JSON
def guardar_conversacion(usuario, asistente, archivo="conversacion.json"):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    
    data.append({"usuario": usuario, "asistente": asistente})
    
    with open(archivo, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def cargar_conversacion(archivo="conversacion.json"):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []

# Interfaz gráfica
class AsistenteVoz(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.engine = configurar_voz()
        self.ultima_respuesta = ""
        self.usuario = "usuario"  # Nombre del usuario (puedes personalizarlo)
    
    def initUI(self):
        self.setWindowTitle("Asistente Conversacional")
        self.setGeometry(100, 100, 400, 300)
        layout = QVBoxLayout()
        
        self.label_instruccion = QLabel("Presiona el botón y habla", self)
        layout.addWidget(self.label_instruccion)
        
        self.boton_hablar = QPushButton("Hablar", self)
        self.boton_hablar.clicked.connect(self.procesar_comando)
        layout.addWidget(self.boton_hablar)
        
        self.label_respuesta = QLabel("", self)
        layout.addWidget(self.label_respuesta)
        
        self.check_voz = QCheckBox("Responder con voz", self)
        self.check_voz.setChecked(True)
        layout.addWidget(self.check_voz)
        
        self.boton_repetir = QPushButton("Repetir última respuesta", self)
        self.boton_repetir.clicked.connect(self.repetir_respuesta)
        layout.addWidget(self.boton_repetir)
        
        self.slider_velocidad = QSlider(Qt.Orientation.Horizontal)
        self.slider_velocidad.setMinimum(100)
        self.slider_velocidad.setMaximum(200)
        self.slider_velocidad.setValue(145)
        self.slider_velocidad.valueChanged.connect(self.cambiar_velocidad)
        layout.addWidget(QLabel("Velocidad de voz"))
        layout.addWidget(self.slider_velocidad)
        
        self.boton_historial = QPushButton("Mostrar Historial", self)
        self.boton_historial.clicked.connect(self.mostrar_historial)
        layout.addWidget(self.boton_historial)
        
        self.setLayout(layout)
    
    def procesar_comando(self):
        self.actualizar_estado("Escuchando...")
        comando = escuchar()
        if comando == "No entendí":
            self.hablar_y_mostrar("Lo siento, no pude entenderte. ¿Podrías repetirlo?")
            return
        respuesta = generar_respuesta_continua(comando, self.usuario)
        self.hablar_y_mostrar(respuesta)
        guardar_conversacion(comando, respuesta)
        self.actualizar_estado("Inactivo")
    
    def hablar_y_mostrar(self, texto):
        self.ultima_respuesta = texto
        self.label_respuesta.setText(f"Asistente: {texto}")
        if self.check_voz.isChecked():
            hablar(self.engine, texto)
    
    def repetir_respuesta(self):
        if self.ultima_respuesta:
            self.hablar_y_mostrar(self.ultima_respuesta)
    
    def cambiar_velocidad(self):
        velocidad = self.slider_velocidad.value()
        self.engine.setProperty('rate', velocidad)
    
    def actualizar_estado(self, estado):
        self.label_instruccion.setText(f"Estado: {estado}")
        QApplication.processEvents()
    
    def mostrar_historial(self):
        historial = cargar_conversacion()
        if not historial:
            self.label_respuesta.setText("No hay historial disponible.")
            return
        
        texto_historial = "\n".join(
            [f"Usuario: {interaccion['usuario']}\nAsistente: {interaccion['asistente']}\n"
             for interaccion in historial]
        )
        self.label_respuesta.setText(f"Historial:\n{texto_historial}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = AsistenteVoz()
    ventana.show()
    sys.exit(app.exec())