import json
from src.agents.prompts import TACTICAL_AGENT_PROMPT

class TacticalPrecisionAgent:
    def __init__(self, llm_client):
        # Aquí pasas tu instancia de Gemini o LangChain
        self.client = llm_client
        self.model = "stepfun/step-3.5-flash:free"

    def generar_instrucciones(self, tarea, metas, duracion):
        # 1. Preparación de contexto (esto ya lo tienes bien)
        metas_dict = [dict(m) for m in metas]
        metas_json = json.dumps(metas_dict, indent=2)

        # 2. Formatear el Prompt
        prompt = TACTICAL_AGENT_PROMPT.format(
            tarea=tarea,
            metas=metas_json,
            duracion=duracion
        )

        # 3. LA CORRECCIÓN: Usar self.client, no self.model
        # Nota: Verifica si tu cliente usa 'generate_content' o 'chat.completions'
        # Si es el cliente oficial de Google/Gemini:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Eres un Arquitecto de Precisión Táctica especializado en protocolos de ejecución."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content