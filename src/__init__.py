import os
import json
import random
import time
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.clock import Clock
from threading import Thread
import pyttsx3
from kivymd.uix.label import MDLabel

class AsistenteApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.historial = []
        self.contexto_activado = False
        self.perfil = {}
        self.alarm_active = False
        self.escuchando = False
        
        # Flags para bucles continuos en respuestas
        self.modo_positivo_activo = False
        self.modo_negativo_activo = False
        
        # Preguntas y consejos personalizados
        self.preguntas_positivas = [
            '¿Qué has aprendido hoy?',
            '¿Cuál fue tu mayor logro reciente?',
            '¿Qué te motiva a seguir adelante?',
            '¿Qué puedes hacer hoy para mejorar mañana?'
        ]
        self.consejos_negativos = [
            'Tómate un respiro, respirar profundo ayuda a calmarte.',
            'Organiza tus ideas, un paso a la vez.',
            'Habla con alguien de confianza, no estás solo.'
        ]
        self.preguntas_entorno = [
            "¿Cómo está tu familia últimamente?",
            "¿Has hablado recientemente con tus amigos?",
            "¿Qué tal va tu trabajo?"
        ]

        # Inicializa el motor de voz (pyttsx3)
        self.voice_engine = pyttsx3.init()
        self.voice_engine.setProperty('voice', 'spanish')

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Light"
        Clock.schedule_interval(self.actualizar_reloj, 1)
        self.cargar_perfil()  # Carga el perfil al iniciar
        return Builder.load_file("interface.kv")

    def actualizar_reloj(self, *args):
        ahora = time.strftime('%H:%M:%S')
        self.root.ids.reloj.text = ahora

    def cambiar_tema(self):
        if self.theme_cls.theme_style == "Light":
            self.theme_cls.theme_style = "Dark"
        else:
            self.theme_cls.theme_style = "Light"

    def agregar_mensaje_historial(self, mensaje):
        label = MDLabel(
            text=mensaje,
            size_hint_y=None,
            height="40dp"
        )
        self.root.ids.historial.add_widget(label)

    def procesar_comando_texto(self):
        """Procesa el comando ingresado en el campo de texto."""
        comando = self.root.ids.input_texto.text.strip()
        if not comando:
            self.agregar_mensaje_historial("Por favor, ingresa un comando.")
            return
        respuesta = self.generar_respuesta(comando)
        self.agregar_mensaje_historial(f"Usuario: {comando}")
        self.agregar_mensaje_historial(f"Asistente: {respuesta}")
        self.hablar(respuesta)
        self.guardar_perfil()  # Guarda el perfil después de cada interacción
        self.root.ids.input_texto.text = ""  # Limpia el campo de texto

    def generar_respuesta(self, comando):
        saludo_respuestas = {
            'buenos dias': '¡Buenos días! ¿Cómo puedo ayudarte hoy?',
            'buenas tardes': '¡Buenas tardes! ¿En qué te puedo ayudar?',
            'buenas noches': '¡Buenas noches! ¿Necesitas algo?',
            'hola': '¡Hola! ¿Cómo estás?'
        }
        for saludo, respuesta in saludo_respuestas.items():
            if saludo in comando.lower():
                return respuesta

        if 'qué hora es' in comando.lower():
            return f"La hora actual es {time.strftime('%H:%M:%S')}"

        if 'analiza contexto' in comando.lower():
            return self.analizar_contexto()

        if 'cómo me llamo' in comando.lower():
            return f"Tu nombre es {self.perfil.get('nombre', 'desconocido')}."

        if 'cuántos años tengo' in comando.lower():
            return f"Tienes {self.perfil.get('edad', 'desconocida')} años."

        if 'de dónde soy' in comando.lower():
            return f"Eres de {self.perfil.get('lugar', 'desconocido')}."

        if 'mis amigos' in comando.lower():
            amigos = ", ".join(self.perfil.get("amigos", ["ninguno"]))
            return f"Tus amigos son: {amigos}."

        if 'mi familia' in comando.lower():
            familia = ", ".join(self.perfil.get("familia", ["ninguno"]))
            return f"Tu familia incluye: {familia}."

        if 'mis intereses' in comando.lower():
            intereses = ", ".join(self.perfil.get("intereses", ["ninguno"]))
            return f"Tus intereses son: {intereses}."

        return "No entendí el comando. Intenta de nuevo."

    def analizar_contexto(self):
        if not self.perfil:
            return "No hay contexto disponible. Activa el contexto primero."
        nombre = self.perfil.get("nombre", "desconocido")
        familia = ", ".join(self.perfil.get("familia", ["ninguno"]))
        amigos = ", ".join(self.perfil.get("amigos", ["ninguno"]))
        intereses = ", ".join(self.perfil.get("intereses", ["ninguno"]))
        lugar = self.perfil.get("lugar", "desconocido")
        return (
            f"Hola, {nombre}. Aquí hay información sobre tu contexto:\n"
            f"- Familia: {familia}\n"
            f"- Amigos: {amigos}\n"
            f"- Intereses: {intereses}\n"
            f"- Lugar de origen: {lugar}"
        )

    def activar_contexto(self):
        if not self.perfil:
            self.agregar_mensaje_historial("No hay perfil. Creando uno nuevo...")
            self.hablar("No hay perfil. Vamos a crear uno nuevo.")
            Thread(target=self.preguntar_datos_perfil, daemon=True).start()
        else:
            self.agregar_mensaje_historial("Modo Contexto activado (ON).")
            self.hablar("Modo Contexto activado. Ahora haré preguntas específicas sobre tu entorno.")
            Thread(target=self.preguntar_entorno, daemon=True).start()
        self.contexto_activado = True

    def cargar_perfil(self):
        if os.path.exists("perfil.json"):
            with open("perfil.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                self.perfil = data["perfil"]
        else:
            self.perfil = {}

    def guardar_perfil(self):
        with open("perfil.json", "w", encoding="utf-8") as file:
            json.dump({"perfil": self.perfil}, file, indent=4, ensure_ascii=False)

    def preguntar_datos_perfil(self):
        try:
            for pregunta in self.preguntas_entorno:
                self.agregar_mensaje_historial(pregunta)
                self.hablar(pregunta)
                respuesta = input("Respuesta: ")  # Simula entrada de texto
                if "nombre" in pregunta.lower():
                    self.perfil["nombre"] = respuesta
                elif "años" in pregunta.lower():
                    self.perfil["edad"] = respuesta
                elif "de dónde" in pregunta.lower():
                    self.perfil["lugar"] = respuesta
                elif "intereses" in pregunta.lower():
                    self.perfil["intereses"] = [resp.strip() for resp in respuesta.split(",")]
                elif "amigos" in pregunta.lower():
                    self.perfil["amigos"] = [resp.strip() for resp in respuesta.split(",")]
                elif "familia" in pregunta.lower():
                    self.perfil["familia"] = [resp.strip() for resp in respuesta.split(",")]
                self.guardar_perfil()
            self.agregar_mensaje_historial("Perfil creado exitosamente.")
            self.hablar("Tu perfil ha sido creado exitosamente.")
        except Exception as e:
            self.agregar_mensaje_historial(f"Error al crear el perfil: {e}")
            self.hablar("Hubo un error al crear tu perfil. Inténtalo de nuevo.")

    def preguntar_entorno(self):
        for pregunta in self.preguntas_entorno:
            self.agregar_mensaje_historial(pregunta)
            self.hablar(pregunta)
            time.sleep(5)  # Espera antes de hacer la siguiente pregunta

    def mostrar_mensaje_positivo(self):
        """Activa o desactiva el modo positivo."""
        if not self.modo_positivo_activo:
            self.modo_positivo_activo = True
            self.agregar_mensaje_historial("Modo Positivo activado.")
            self.hablar("Modo Positivo activado.")
            Clock.schedule_interval(self.loop_respuestas_positivas, 10)  # Ejecuta cada 10 segundos
        else:
            self.modo_positivo_activo = False
            self.agregar_mensaje_historial("Modo Positivo desactivado.")
            self.hablar("Modo Positivo desactivado.")

    def loop_respuestas_positivas(self, dt):
        """Bucle para generar respuestas positivas continuas."""
        if not self.modo_positivo_activo:
            return False  # Detiene el bucle si el modo está desactivado
        mensaje = random.choice(self.preguntas_positivas)
        if self.contexto_activado:
            mensaje = f"{self.perfil.get('nombre', 'desconocido')}, {mensaje}"
        self.agregar_mensaje_historial(mensaje)
        self.hablar(mensaje)

    def mostrar_mensaje_negativo(self):
        """Activa o desactiva el modo negativo."""
        if not self.modo_negativo_activo:
            self.modo_negativo_activo = True
            self.agregar_mensaje_historial("Modo Negativo activado.")
            self.hablar("Modo Negativo activado.")
            Clock.schedule_interval(self.loop_respuestas_negativas, 10)  # Ejecuta cada 10 segundos
        else:
            self.modo_negativo_activo = False
            self.agregar_mensaje_historial("Modo Negativo desactivado.")
            self.hablar("Modo Negativo desactivado.")

    def loop_respuestas_negativas(self, dt):
        """Bucle para generar respuestas negativas continuas."""
        if not self.modo_negativo_activo:
            return False  # Detiene el bucle si el modo está desactivado
        mensaje = random.choice(self.consejos_negativos)
        if self.contexto_activado:
            mensaje = f"{self.perfil.get('nombre', 'desconocido')}, {mensaje}"
        self.agregar_mensaje_historial(mensaje)
        self.hablar(mensaje)

    def hablar(self, texto):
        try:
            self.voice_engine.say(texto)
            self.voice_engine.runAndWait()
        except Exception as e:
            print(f"Error al reproducir voz: {e}")

if __name__ == "__main__":
    AsistenteApp().run()