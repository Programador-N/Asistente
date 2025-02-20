import os
import json
import random
import time
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.clock import Clock
from threading import Thread
from vosk import Model, KaldiRecognizer
import wave
import pyttsx3
from kivymd.uix.label import MDLabel
from kivy.animation import Animation
from kivy.properties import ListProperty

class AsistenteApp(MDApp):
    divider_color = ListProperty([0.5, 0.5, 0.5, 1])  # Color inicial de la línea divisoria (gris)
    avatar_color = ListProperty([1, 1, 1, 1])  # Color inicial del avatar (blanco)
    avatar_animation_speed = 0.5  # Velocidad inicial del salto del avatar

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
        
        self.preguntas_positivas = [
            '¿Qué has aprendido hoy?',
            '¿Cuál fue tu mayor logro reciente?',
            '¿Qué te motiva a seguir adelante?',
            '¿Qué puedes hacer hoy para mejorar mañana?',
            '¿Cuál es el plan para alcanzar tus metas?',
            '¿Qué pasos tomarás para lograr el éxito?',
            '¿Qué te inspira a ser mejor cada día?',
            '¿Cómo puedes transformar un desafío en oportunidad?',
            '¿Qué pequeño avance has logrado hoy?',
            '¿Qué te hace sentir orgulloso de ti mismo?'
        ]
        self.consejos_negativos = [
            'Tómate un respiro, respirar profundo ayuda a calmarte.',
            'Organiza tus ideas, un paso a la vez.',
            'Habla con alguien de confianza, no estás solo.',
            'Descansa un poco, tu bienestar es importante.',
            'Recuerda que es normal tener días difíciles.',
            'No te presiones demasiado, todos tenemos momentos complicados.',
            'Permítete sentir y luego busca soluciones.',
            'Confía en que mañana será un nuevo comienzo.',
            'Considera tomar un pequeño descanso para recargar energías.',
            'Cada obstáculo es una oportunidad para crecer.'
        ]
        self.preguntas_entorno = [
            "¿Cómo está tu familia últimamente?",
            "¿Has hablado recientemente con tus amigos?",
            "¿Qué tal va tu trabajo?",
            "¿Has aprendido algo nuevo relacionado con tus intereses?",
            "¿Cómo te sientes respecto a tu entorno actual?"
        ]
        self.consejos_entorno = [
            "Recuerda que tu familia siempre estará ahí para apoyarte.",
            "Mantén el contacto con tus amigos, son importantes en tu vida.",
            "Organiza tus tareas laborales para mejorar tu productividad.",
            "Explora tus intereses para seguir creciendo como persona.",
            "Tu entorno influye mucho en tu bienestar. Asegúrate de cuidarlo."
        ]
        
        # Inicializa el motor de voz (pyttsx3) una sola vez y configúralo
        self.voice_engine = pyttsx3.init()
        voices = self.voice_engine.getProperty('voices')
        # Selecciona una voz (puedes ajustar el índice o filtrar por palabra clave)
        if len(voices) > 1:
            self.voice_engine.setProperty('voice', voices[1].id)
        else:
            self.voice_engine.setProperty('voice', voices[0].id)
        self.voice_engine.setProperty('rate', 145)

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Light"
        Clock.schedule_interval(self.actualizar_reloj, 1)
        Clock.schedule_once(self.animate_divider, 1)  # Iniciar animación de la línea divisoria
        Clock.schedule_once(self.animar_avatar_inicial, 1)  # Iniciar animación inicial del avatar
        return Builder.load_file("interface.kv")

    def actualizar_reloj(self, *args):
        try:
            ahora = time.strftime('%H:%M:%S')
            # Actualiza el widget en el hilo principal
            Clock.schedule_once(lambda dt: setattr(self.root.ids.reloj, 'text', ahora))
        except Exception as e:
            print(f"Error actualizando el reloj: {e}")

    def cambiar_tema(self):
        self.theme_cls.theme_style = "Dark" if self.theme_cls.theme_style == "Light" else "Light"

    def actualizar_avatar(self, estado):
        try:
            if estado == "positivo":
                self.avatar_color = [0, 1, 0, 1]  # Verde
                self.root.ids.avatar.source = "assets/positivo.png"
                self.avatar_animation_speed = 0.2  # Salta más rápido
            elif estado == "negativo":
                self.avatar_color = [1, 0, 0, 1]  # Rojo
                self.root.ids.avatar.source = "assets/negativo.png"
                self.avatar_animation_speed = 1.0  # Salta más lento
            else:
                self.avatar_color = [1, 1, 1, 1]  # Blanco
                self.root.ids.avatar.source = "assets/neutral.png"
                self.avatar_animation_speed = 0.5  # Velocidad predeterminada
            self.animar_avatar()  # Reinicia la animación con la nueva velocidad
        except Exception as e:
            print(f"Error al actualizar el avatar: {e}")

    def animar_avatar_inicial(self, dt=None):
        self.animar_avatar()

    def animar_avatar(self):
        try:
            anim_up = Animation(pos_hint={"center_y": 0.6}, duration=self.avatar_animation_speed)
            anim_down = Animation(pos_hint={"center_y": 0.5}, duration=self.avatar_animation_speed)
            anim = anim_up + anim_down
            anim.repeat = True
            anim.start(self.root.ids.avatar_box)
        except Exception as e:
            print(f"Error en animar_avatar: {e}")

    def agregar_mensaje_historial(self, mensaje):
        try:
            label = MDLabel(text=mensaje, size_hint_y=None, height="40dp")
            # Actualiza la UI desde el hilo principal
            Clock.schedule_once(lambda dt: self.root.ids.historial.add_widget(label))
            Clock.schedule_once(lambda dt: self.root.ids.historial.parent.scroll_to(label))
        except Exception as e:
            print(f"Error agregando mensaje al historial: {e}")

    def procesar_comando(self):
        self.agregar_mensaje_historial("Escuchando...")
        self.escuchando = True
        Thread(target=self.escuchar, daemon=True).start()

    def escuchar(self):
        try:
            model = Model("vosk-model-small-es-0.22")  # Asegúrate de tener este modelo descargado
            rec = KaldiRecognizer(model, 16000)
            
            with wave.open("temp_audio.wav", "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                with wave.open("test.wav", "rb") as rf:
                    wf.writeframes(rf.readframes(rf.getnframes()))

            with wave.open("temp_audio.wav", "rb") as wf:
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.FinalResult())
                        comando = result.get('text', '').lower()
                        print(f"Entendí: {comando}")
                        respuesta = self.generar_respuesta(comando)
                        self.agregar_mensaje_historial(f"Usuario: {comando}")
                        self.agregar_mensaje_historial(f"Asistente: {respuesta}")
                        self.hablar(respuesta)
            self.escuchando = False
        except Exception as e:
            self.escuchando = False
            self.agregar_mensaje_historial(f"Error en escuchar: {e}")

    def generar_respuesta(self, comando):
        saludo_respuestas = {
            'buenos dias': '¡Buenos días! ¿Cómo puedo ayudarte hoy?',
            'buenas tardes': '¡Buenas tardes! ¿En qué te puedo ayudar?',
            'buenas noches': '¡Buenas noches! ¿Necesitas algo?',
            'hola': '¡Hola! ¿Cómo estás?'
        }
        for saludo, respuesta in saludo_respuestas.items():
            if saludo in comando:
                return respuesta

        if 'qué hora es' in comando:
            return f"La hora actual es {time.strftime('%H:%M:%S')}"

        if 'qué día es hoy' in comando:
            return f"Hoy es {time.strftime('%d/%m/%Y')}"

        if 'analiza contexto' in comando:
            return self.analizar_contexto()

        if 'establecer alarma' in comando:
            return "Alarma establecida."

        return "No entendí el comando. Intenta de nuevo."

    def analizar_contexto(self):
        if not self.perfil:
            return "No hay contexto disponible. Activa el contexto primero."
        nombre = self.perfil.get("nombre", "desconocido")
        familia = ", ".join(self.perfil["familia"])
        amigos = ", ".join(self.perfil["amigos"])
        trabajo = ", ".join(self.perfil["trabajo"])
        return (
            f"Hola, {nombre}. Aquí hay información sobre tu contexto:\n"
            f"- Familia: {familia}\n"
            f"- Amigos: {amigos}\n"
            f"- Trabajo: {trabajo}"
        )

    def activar_contexto(self):
        if self.contexto_activado:
            self.contexto_activado = False
            self.agregar_mensaje_historial("Modo Contexto desactivado (OFF).")
            self.hablar("Modo Contexto desactivado.")
        else:
            if os.path.exists("contexto.json"):
                self.cargar_perfil()
                self.agregar_mensaje_historial("Modo Contexto activado (ON).")
                self.hablar("Modo Contexto activado. Ahora haré preguntas específicas sobre tu entorno.")
                Thread(target=self.preguntar_entorno, daemon=True).start()
            else:
                self.agregar_mensaje_historial("No se encontró un contexto. Creando uno nuevo...")
                self.hablar("No se encontró un contexto. Vamos a crear uno nuevo.")
                Thread(target=self.preguntar_datos_perfil, daemon=True).start()
            self.contexto_activado = True

    def cargar_perfil(self):
        with open("contexto.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            self.perfil = data["perfil"]

    def preguntar_datos_perfil(self):
        self.perfil = {
            "nombre": "Programadorene",
            "familia": ["Silvana (mamá)", "Salim (hermano)", "Papá de mi hermano (tío)"],
            "amigos": ["Agustín", "Martín", "Zekki", "Yoel", "Paolo"],
            "trabajo": ["Sonia (encargada)", "Emma (encargado)", "Anna (compañera)", "Guada (compañera)", "Gonza (compañero)"]
        }
        with open("contexto.json", "w", encoding="utf-8") as file:
            json.dump({"perfil": self.perfil}, file, indent=4, ensure_ascii=False)

    def preguntar_entorno(self):
        for pregunta in self.preguntas_entorno:
            self.agregar_mensaje_historial(pregunta)
            self.hablar(pregunta)
            respuesta = "Respuesta simulada"
            self.agregar_mensaje_historial(f"Respuesta: {respuesta}")
            self.hablar(f"Entendido, has dicho: {respuesta}.")
        self.agregar_mensaje_historial("Hemos terminado de hablar sobre tu entorno.")
        self.hablar("Hemos terminado de hablar sobre tu entorno.")

    def mostrar_mensaje_positivo(self):
        # Toggle para respuestas positivas continuas
        if not self.modo_positivo_activo:
            self.modo_positivo_activo = True
            Thread(target=self.loop_respuestas_positivas, daemon=True).start()
        else:
            self.modo_positivo_activo = False

    def loop_respuestas_positivas(self):
        while self.modo_positivo_activo:
            mensaje = random.choice(self.preguntas_positivas)
            if self.contexto_activado:
                mensaje = f"{self.perfil.get('nombre', 'desconocido')}, {mensaje}"
            Clock.schedule_once(lambda dt: self.agregar_mensaje_historial(mensaje))
            self.hablar(mensaje)
            self.actualizar_avatar("positivo")
            time.sleep(10)

    def mostrar_mensaje_negativo(self):
        # Toggle para respuestas negativas continuas
        if not self.modo_negativo_activo:
            self.modo_negativo_activo = True
            Thread(target=self.loop_respuestas_negativas, daemon=True).start()
        else:
            self.modo_negativo_activo = False

    def loop_respuestas_negativas(self):
        while self.modo_negativo_activo:
            mensaje = random.choice(self.consejos_negativos)
            if self.contexto_activado:
                mensaje = f"{self.perfil.get('nombre', 'desconocido')}, {mensaje}"
            Clock.schedule_once(lambda dt: self.agregar_mensaje_historial(mensaje))
            self.hablar(mensaje)
            self.actualizar_avatar("negativo")
            time.sleep(10)

    def hablar(self, texto):
        try:
            self.voice_engine.say(texto)
            self.voice_engine.runAndWait()
        except Exception as e:
            print(f"Error al reproducir voz: {e}")

    def validate_time(self, time_str):
        try:
            time.strptime(time_str, '%H:%M')
        except ValueError:
            self.agregar_mensaje_historial('Formato incorrecto, usa HH:MM')

    def set_alarm(self):
        alarm_time = self.root.ids.alarm_time.text
        try:
            hours, minutes = map(int, alarm_time.split(':'))
            now = time.localtime()
            alarm_seconds = hours * 3600 + minutes * 60
            now_seconds = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
            if alarm_seconds < now_seconds:
                alarm_seconds += 86400  # Alarma para el día siguiente
            seconds = alarm_seconds - now_seconds
            Clock.schedule_once(lambda dt: self.trigger_alarm(), seconds)
            self.root.ids.countdown.text = f'Tiempo restante: {seconds // 3600:02d}:{(seconds % 3600) // 60:02d}'
            Clock.schedule_interval(self.update_countdown, 1)
        except ValueError:
            self.agregar_mensaje_historial('Formato incorrecto, usa HH:MM')

    def update_countdown(self, dt):
        current_text = self.root.ids.countdown.text
        try:
            # Se asume el formato: "Tiempo restante: HH:MM"
            parts = current_text.split(':')
            hours = int(parts[1])
            minutes = int(parts[2])
            total_seconds = hours * 3600 + minutes * 60
            if total_seconds > 0:
                total_seconds -= 1
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.root.ids.countdown.text = f'Tiempo restante: {hours:02d}:{minutes:02d}'
            else:
                self.root.ids.countdown.text = '¡Alarma!'
                self.trigger_alarm()
                return False  # Detiene la actualización
        except Exception as e:
            print(f"Error actualizando cuenta regresiva: {e}")

    def trigger_alarm(self):
        self.agregar_mensaje_historial('¡Alarma sonando!')
        self.hablar('¡Alarma!')

    def toggle_alarm_state(self):
        self.alarm_active = not self.alarm_active

    def animate_divider(self, dt=None, *args):
        try:
            new_color = random.choice([
                [0.6, 0.8, 1, 1],  # Azul claro
                [0.9, 0.6, 0.2, 1],  # Naranja
                [0.5, 0.7, 0.5, 1],  # Verde suave
                [0.8, 0.4, 0.6, 1],  # Rosa pastel
            ])
            anim = Animation(divider_color=new_color, duration=3)
            anim.bind(on_complete=self.animate_divider)
            anim.start(self)
        except Exception as e:
            print(f"Error en animate_divider: {e}")

if __name__ == "__main__":
    import time
    # Bucle de reinicio automático en caso de cierre inesperado
    while True:
        try:
            AsistenteApp().run()
            break  # Si se cierra de forma intencional, sal del bucle
        except Exception as e:
            print("La aplicación se cerró inesperadamente:", e)
            time.sleep(1)
