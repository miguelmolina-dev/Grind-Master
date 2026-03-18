import json
from src.agents.prompts import DATA_CLERK_PROMPT


class RegistrarBot:
    def __init__(self, llm_client):
        self.client = llm_client
        self.model = "stepfun/step-3.5-flash:free"

    def process_entry(self, categoria, evento, solucion, dificultad, meta_id=None):
        # Asegúrate de pasar 'dificultad' explícitamente en el prompt
        raw_input = f"Categoría: {categoria}, Evento: {evento}, Solución: {solucion}, Dificultad: {dificultad}"
    
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": f"""
            Analiza esta actividad respecto a la meta {meta_id}.
            Responde EXCLUSIVAMENTE en formato JSON con estas claves:
            {{"categoria": "{categoria}", "evento": "{evento}", "solucion": "{solucion}", 
              "dificultad": {dificultad}, "analisis_cognitivo": "tu analisis", 
              "pregunta_reflexiva": "tu pregunta"}}
            """}]
        )
        # Parseo seguro

        try:
            return json.loads(response.choices[0].message.content)
        except:
            return None # Esto detendrá el flujo y evitará el error en DB
