import json
from datetime import datetime
from src.agents.prompts import PROMPT_GRIND_MASTER, PROMPT_EJECUTOR_DIARIO
from src.utils.model_config import DEFAULT_MODEL

class GrindMaster:
    def __init__(self, llm_client):
        self.client = llm_client
        self.system_prompt = PROMPT_GRIND_MASTER
        self.model = DEFAULT_MODEL

    def generar_plan(self, metas, horas_dw, restricciones):
        # Convertimos las metas a una cadena legible
        metas_contexto = json.dumps(metas, ensure_ascii=False, indent=2)
        
        user_prompt = PROMPT_EJECUTOR_DIARIO.format(metas_contexto=metas_contexto, horas_dw=horas_dw, restricciones=json.dumps(restricciones))

        try:
            response = self.client.chat.completions.create(
                model=self.model, # Optimizado para latencia y JSON
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": f"Fallo en la matriz de planificación: {e}"}