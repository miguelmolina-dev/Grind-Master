import json
import re
from src.agents.prompts import PROMPT_VALIDADOR, PROMPT_EXTRACTOR, PROMPT_MENTOR
import concurrent.futures

class MetaArchitect:
    def __init__(self, llm_client):
        self.client = llm_client
        self.model = "stepfun/step-3.5-flash:free"

    def _llamar_llm_json(self, system_prompt, user_content):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1 # Mínima aleatoriedad para evitar alucinaciones de formato
            )
            raw_content = response.choices[0].message.content
            
            # Limpieza agresiva de Markdown
            raw_content = raw_content.replace("```json", "").replace("```", "").strip()
            
            match = re.search(r"(\{.*\})", raw_content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            
            # Si no hay JSON pero hay texto, lo envolvemos nosotros
            return {"texto": raw_content, "memoria_actualizada": "Sin cambios", "aprobado": False}
    
        except Exception as e:
            # NUNCA devolver None, devolver un objeto de estructura válida
            return {"texto": f"Error técnico: {str(e)}", "aprobado": False}

    def extraer_y_preguntar(self, entrada_usuario, snapshot_json, historial_completo, memoria_estrategica):
        """
        Orquesta la lógica del Triunvirato manejando el historial filtrado (Solo Usuario).
        """
        # 1. Manejo del Caso Base (Día 0)
        # Si historial_completo está vacío o no es una lista, inicializamos
        if not historial_completo or not isinstance(historial_completo, list):
            contexto_usuario = "No hay historial previo. Esta es la primera interacción."
        else:
            # Unimos los mensajes de usuario (que vienen como strings) en un bloque
            contexto_usuario = "\n".join([f"- {msg}" for msg in historial_completo])

        # 2. Construcción del input optimizado (Sin el ruido de las respuestas del Agente)
        input_data = f"""
        MEMORIA ESTRATÉGICA ACUMULADA: {memoria_estrategica}
        DATOS ACTUALES DE LA META: {json.dumps(snapshot_json)}
        
        REQUERIMIENTOS DEL USUARIO (Últimos mensajes):
        {contexto_usuario}
        
        INTERVENCIÓN ACTUAL: {entrada_usuario}
        
        INSTRUCCIÓN: Responde exclusivamente en formato JSON.
        """

        # 3. Ejecución Paralela (El Triunvirato)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_extractor = executor.submit(self._llamar_llm_json, PROMPT_EXTRACTOR, input_data)
            future_validador = executor.submit(self._llamar_llm_json, PROMPT_VALIDADOR, input_data)
            future_mentor = executor.submit(self._llamar_llm_json, PROMPT_MENTOR, input_data)

            try:
                entregable = future_extractor.result()
                validacion = future_validador.result()
                mentor_resp = future_mentor.result()
            except Exception as e:
                print(f"Fallo en ejecución paralela: {e}")
                return None

        # 4. Consolidación y Prevención de NoneTypes
        if not mentor_resp:
            return None

        # BUSQUEDA MULTI-LLAVE (Blindaje)
        # Buscamos 'texto_para_usuario' (según tu prompt) o 'texto' (por estándar)
        texto_final = mentor_resp.get("texto_para_usuario") or mentor_resp.get("texto")
        
        if not texto_final:
            # Si el LLM devolvió el JSON pero con otra llave, o texto plano
            texto_final = "He procesado tu entrada, pero hubo un error de formato en mi respuesta técnica."

        return {
            "texto": texto_final,
            "memoria": mentor_resp.get("memoria_actualizada", memoria_estrategica),
            "aprobado": validacion.get("aprobado", False) if validacion else False,
            "entregable": entregable if entregable else snapshot_json
        }

    def parsear_respuesta_hibrida(self, respuesta_raw):
        match = re.search(r"```json\n(.*?)\n```", respuesta_raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                texto_chat = respuesta_raw.replace(match.group(0), "").strip()
                # Retornamos los 3 valores explícitamente
                return texto_chat, data.get("memoria_actualizada"), data.get("entregable_db")
            except json.JSONDecodeError:
                return "Error en el formato JSON", None, None
        return respuesta_raw, None, None
        

    def generar_memoria_resumen(self, historial):
        """Resume la conversación en un objeto de memoria para el contexto."""
        contexto = "\n".join([f"{m['role']}: {m['content']}" for m in historial])
        prompt = f"""
        Resume esta conversación estratégica para que el Goal Architect sepa dónde estamos.
        Devuelve SOLO un JSON con:
        - "paso": (int) el paso de Tracy en el que estamos.
        - "datos_clave": (dict) los datos que ya tenemos (nombre, fecha, etc).
        - "pendientes": (list) lo que falta preguntar.
        - "tono": (str) estado emocional del usuario.
        
        Conversación: {contexto}
        """
        # Aquí llamarías a tu LLM para obtener este JSON de memoria
        # Por simplicidad en la lógica, asumiremos que devuelve el dict
        return self.client.generate_json(prompt)
