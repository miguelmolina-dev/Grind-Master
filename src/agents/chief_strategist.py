from src.agents.prompts import STRATEGIC_SYSTEM_PROMPT, MODES
from src.utils.model_config import DEFAULT_MODEL

class ChiefStrategist:
    def __init__(self, llm_client):
        self.system_prompt = STRATEGIC_SYSTEM_PROMPT
        self.client = llm_client
        self.role = "Consultor de Alto Rendimiento"
        self.model = DEFAULT_MODEL

    def conduct_audit(self, data_rows, mode="short_term"):
        # Convertir datos a texto
        contexto_ejecucion = "\n".join([str(row) for row in data_rows])
        
        # Formatear el prompt centralizado
        final_prompt = STRATEGIC_SYSTEM_PROMPT.format(
            mode=mode,
            context_instructions=MODES[mode]["desc"]
        )
        
        # Llamada a la API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": final_prompt},
                {"role": "user", "content": f"Analiza estos registros:\n{contexto_ejecucion}"}
            ]
        )
        return response.choices[0].message.content
    
    def continue_dialogue(self, history):
        """
        Envía el historial acumulado a Claude para mantener el contexto dialéctico.
        History es una lista de diccionarios: [{"role": "user", "content": "..."}]
        """
        messages = [{"role": "system", "content": STRATEGIC_SYSTEM_PROMPT}] + history
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content