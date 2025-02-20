import threading
import datetime
import os
import json
import speech_recognition as sr
import pyttsx3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.slider import Slider
from kivy.clock import Clock

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

# Interfaz gráfica con Kivy
class AsistenteVozApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = configurar_voz()
        self.ultima_respuesta = ""
        self.usuario = "usuario"  # Nombre del usuario (puedes personalizarlo)
        self.modo_conversacion = None  # Puede ser "verde" o "rojo"
        self.contador_preguntas_verde = 0  # Contador para preguntas en modo verde

    def build(self):
        self.title = "Asistente Conversacional"
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Reloj
        self.reloj_label = Label(text="Hora actual: --:--:--", size_hint_y=None, height=40)
        layout.add_widget(self.reloj_label)
        Clock.schedule_interval(self.actualizar_reloj, 1)  # Actualiza el reloj cada segundo
        
        # Instrucciones
        self.label_instruccion = Label(text="Presiona un botón para comenzar", size_hint_y=None, height=40)
        layout.add_widget(self.label_instruccion)
        
        # Botón Verde
        self.boton_verde = Button(text="Verde: Quiero ayuda o saber cómo estoy", background_color=(0, 1, 0, 1))
        self.boton_verde.bind(on_press=self.iniciar_conversacion_verde)
        layout.add_widget(self.boton_verde)
        
        # Botón Rojo
        self.boton_rojo = Button(text="Rojo: No quiero ayuda y estoy sin energías", background_color=(1, 0, 0, 1))
        self.boton_rojo.bind(on_press=self.iniciar_conversacion_rojo)
        layout.add_widget(self.boton_rojo)
        
        # Botón Hablar
        self.boton_hablar = Button(text="Hablar")
        self.boton_hablar.bind(on_press=self.procesar_comando)
        layout.add_widget(self.boton_hablar)
        
        # Respuesta del Asistente
        self.label_respuesta = Label(text="", size_hint_y=None, height=80)
        layout.add_widget(self.label_respuesta)
        
        # Checkbox para responder con voz
        self.check_voz = CheckBox(active=True)
        self.check_voz_label = Label(text="Responder con voz", size_hint_y=None, height=40)
        layout.add_widget(self.check_voz)
        layout.add_widget(self.check_voz_label)
        
        # Slider de velocidad de voz
        self.slider_velocidad = Slider(min=100, max=200, value=145)
        self.slider_velocidad.bind(value=self.cambiar_velocidad)
        layout.add_widget(Label(text="Velocidad de voz"))
        layout.add_widget(self.slider_velocidad)
        
        # Botón Mostrar Historial
        self.boton_historial = Button(text="Mostrar Historial")
        self.boton_historial.bind(on_press=self.mostrar_historial)
        layout.add_widget(self.boton_historial)
        
        return layout

    def actualizar_reloj(self, dt):
        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
        self.reloj_label.text = f"Hora actual: {hora_actual}"

    def iniciar_conversacion_verde(self, instance):
        self.modo_conversacion = "verde"
        self.actualizar_estado("Iniciando conversación de ayuda...")
        
        # Incrementar contador de preguntas
        self.contador_preguntas_verde += 1
        
        # Elegir pregunta según el contador
        if self.contador_preguntas_verde == 1:
            mensaje = f"{obtener_prompt_por_hora()} {PROMPTS_CONVERSACION['preguntas_iniciales'][0]}"
        elif self.contador_preguntas_verde == 2:
            mensaje = PROMPTS_CONVERSACION["preguntas_seguimiento"][0]
        elif self.contador_preguntas_verde == 3:
            mensaje = PROMPTS_CONVERSACION["preguntas_seguimiento"][1]
        else:
            mensaje = "¿Hay algo más en lo que pueda ayudarte hoy?"
        
        self.hablar_y_mostrar(mensaje)

    def iniciar_conversacion_rojo(self, instance):
        self.modo_conversacion = "rojo"
        self.actualizar_estado("Iniciando conversación de baja energía...")
        mensaje = "Entiendo que no tienes energías en este momento. Si necesitas algo, estaré aquí cuando quieras hablar."
        self.hablar_y_mostrar(mensaje)

    def procesar_comando(self, instance):
        self.actualizar_estado("Escuchando...")
        comando = escuchar()
        if comando == "No entendí":
            self.hablar_y_mostrar("Lo siento, no pude entenderte. ¿Podrías repetirlo?")
            return
        
        if self.modo_conversacion == "verde":
            respuesta = generar_respuesta_continua(comando, self.usuario)
            self.hablar_y_mostrar(respuesta)
        elif self.modo_conversacion == "rojo":
            if "ayuda" in comando or "sucede" in comando:
                respuesta = "Entiendo que algo te preocupa. ¿Quieres contarme más?"
                self.hablar_y_mostrar(respuesta)
            else:
                respuesta = "Estoy aquí si necesitas algo. Solo dime."
                self.hablar_y_mostrar(respuesta)
        else:
            respuesta = "Selecciona un modo (verde o rojo) para continuar."
            self.hablar_y_mostrar(respuesta)
        
        guardar_conversacion(comando, respuesta)
        self.actualizar_estado("Inactivo")

    def hablar_y_mostrar(self, texto):
        self.ultima_respuesta = texto
        self.label_respuesta.text = f"Asistente: {texto}"
        if self.check_voz.active:
            hablar(self.engine, texto)

    def cambiar_velocidad(self, instance, value):
        self.engine.setProperty('rate', value)

    def actualizar_estado(self, estado):
        self.label_instruccion.text = f"Estado: {estado}"

    def mostrar_historial(self, instance):
        historial = cargar_conversacion()
        if not historial:
            self.label_respuesta.text = "No hay historial disponible."
            return
        
        texto_historial = "\n".join(
            [f"Usuario: {interaccion['usuario']}\nAsistente: {interaccion['asistente']}\n"
             for interaccion in historial]
        )
        self.label_respuesta.text = f"Historial:\n{texto_historial}"

if __name__ == "__main__":
    AsistenteVozApp().run()