import pyttsx3
from faster_whisper import WhisperModel
from src.database.manager import DatabaseManager
from src.agents.prompts import COACH_PAIN_PROMPT
import json
import subprocess
import os

class IronCoach:
    def __init__(self, llm_client, db: DatabaseManager):
        self.client = llm_client
        self.db = db
        self.model = "google/gemini-2.0-flash-001"
        self.model_path = r"G:\Proyectos_Python\resolvers-log\src\utils\voice_models\en_US-norman-medium.onnx"
        self.config_path = r"G:\Proyectos_Python\resolvers-log\src\utils\voice_models\en_US-norman-medium.onnx.json"
        
        # --- CONFIGURACIÓN LOCAL ---
        # STT: Cargamos Whisper en local (usando CPU o GPU 'cuda')
        # El modelo 'base' es rápido y suficiente para el gym
        self.stt_model = WhisperModel("base", device="cpu", compute_type="int8")
        
        # TTS: Motor de voz local
        self.tts_engine = pyttsx3.init()
        self._configurar_voz_autoritaria()

    def _configurar_voz_autoritaria(self):
        """Ajusta el tono de Coach Pain."""
        voices = self.tts_engine.getProperty('voices')
        # Intentar buscar una voz masculina/grave
        self.tts_engine.setProperty('voice', voices[0].id) 
        self.tts_engine.setProperty('rate', 160) # Velocidad de habla

    def _transcribir_audio_local(self, path):
        """STT sin depender de OpenRouter."""
        segments, info = self.stt_model.transcribe(path, beam_size=5)
        return " ".join([segment.text for segment in segments])

    def _generar_voz_local(self, texto, output_path="response.wav"):
        """Genera el audio en un archivo local."""
        self.tts_engine.save_to_file(texto, output_path)
        self.tts_engine.runAndWait()
        return output_path

    def procesar_entrenamiento(self, audio_path, grupo_actual):
        # 1. STT Local
        transcripcion = self._transcribir_audio_local(audio_path)
        
        # 2. IA (Mantenemos OpenRouter por potencia de razonamiento)
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": COACH_PAIN_PROMPT},
                {"role": "user", "content": f"Reporte: {transcripcion}. Grupo: {grupo_actual}"}
            ],
            response_format={ "type": "json_object" }
        )
        
        datos = self._parse_json(response.choices[0].message.content)
    
        # USAR .get() CON VALORES POR DEFECTO PARA EVITAR EL KEYERROR
        ejercicio = datos.get('ejercicio', 'Ejercicio no detectado')
        peso = datos.get('peso', 0)
        reps = datos.get('reps', 0)
        feedback = datos.get('feedback', "Buen esfuerzo, sigue así.")

        # Persistencia protegida
        try:
            self.db.execute_action("""
                INSERT INTO registro_entrenamientos (ejercicio_nombre, grupo_muscular, peso_real, reps_reales)
                VALUES (?, ?, ?, ?)
            """, (ejercicio, grupo_actual, peso, reps))
        except Exception as e:
            print(f"Error al guardar en DB: {e}")

        # Generar voz con el feedback seguro
        audio_file = self._generar_voz_local(feedback)
            
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()

        return {
            "texto": datos['feedback'],
            "audio": audio_bytes,
            "es_record": False # Lógica de comparación pendiente
        }
    
    def _parse_json(self, text):
        """Extrae de forma robusta el JSON de la respuesta de la IA."""
        import json
        import re
        try:
            # Busca cualquier cosa entre llaves { } incluyendo saltos de línea
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {}
        except Exception as e:
            print(f"Error parseando JSON: {e}")
            return {}
        
    def procesar_serie_directa(self, datos, grupo_actual):
        """Analiza la progresión comparando con el último registro."""
        
        # 1. BUSCAR EL REGISTRO ANTERIOR (Memoria del sistema)
        query_historial = """
            SELECT peso_real, reps_reales, fecha 
            FROM registro_entrenamientos 
            WHERE ejercicio_nombre = ? 
            ORDER BY fecha DESC LIMIT 1
        """
        ultimo_log = self.db.execute_query_dict(query_historial, (datos['ejercicio'],))

        # 2. CALCULAR PROGRESIÓN
        contexto_progresion = ""
        if ultimo_log:
            last = ultimo_log[0]
            contexto_progresion = (
                f"En la sesión anterior ({last['fecha']}), hizo {last['peso_real']}kg x {last['reps_reales']} reps. "
                f"Hoy ha hecho {datos['peso']}kg x {datos['reps']} reps."
            )
        else:
            contexto_progresion = "Este es el primer registro de este ejercicio. Estableciendo línea base."

        # 3. LLAMADA AL MODELO CON CONTEXTO COMPARATIVO
        prompt_usuario = (
            f"Analiza mi progresión en {datos['ejercicio']}. "
            f"{contexto_progresion} "
            f"{datos['reps']} reps a {datos['peso']}kg. "
            f"¿Llegó al fallo? {'Sí' if datos['fallo'] else 'No'}. "
            f"Dame un feedback corto y agresivo."
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": COACH_PAIN_PROMPT},
                {"role": "user", "content": prompt_usuario}
            ]
        )

        # 4. PERSISTENCIA (Después del análisis para no compararse consigo mismo)
        self.db.execute_action("""
            INSERT INTO registro_entrenamientos 
            (ejercicio_nombre, grupo_muscular, peso_real, reps_reales, fallo_alcanzado)
            VALUES (?, ?, ?, ?, ?)
        """, (datos['ejercicio'], grupo_actual, datos['peso'], datos['reps'], datos['fallo']))

        res_json = self._parse_json(response.choices[0].message.content)
        return res_json.get('coach_response', "Datos registrados. Sigue.")

    def hablar_feedback(self, texto):
        """Método opcional para mantener el TTS local."""
        audio_path = self.generar_voz_local(texto)
        return audio_path
        # Aquí podrías usar st.audio en la UI para reproducirlo
    
    def generar_voz_local(self, texto, output_filename="feedback.wav"):
        """Genera audio neuronal usando Piper con rutas robustas."""
        try:
            piper_exe = r"G:\Proyectos_Python\resolvers-log\.venv\Scripts\piper.exe"
            # 1. Definimos la ruta de salida absoluta para evitar el NoneType
            base_dir = os.path.dirname(os.path.abspath(__file__))
            full_output_path = os.path.join(base_dir, "..", "..", output_filename)
            
            # 2. Comando usando la ruta exacta que te funcionó en la terminal
            comando = [
                piper_exe, # Si falla, cámbialo por la ruta completa al piper.exe
                "--model", self.model_path,
                "--output_file", full_output_path,
                "--length_scale", "0.8"
            ]
            
            # 3. Ejecución con captura de errores para debug
            process = subprocess.Popen(
                comando, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                shell=True # Importante en Windows para reconocer comandos del PATH
            )
            
            stdout, stderr = process.communicate(input=texto.encode('utf-8'))
            
            if process.returncode != 0:
                print(f"DEBUG ERROR PIPER: {stderr.decode()}")
                return None
                
            return full_output_path # Retornamos el path completo

        except Exception as e:
            print(f"DEBUG EXCEPTION: {e}")
            return None