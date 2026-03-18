# src/agents/agency.py
from src.agents.registrar_bot import RegistrarBot
from src.agents.chief_strategist import ChiefStrategist
import os
from openai import OpenAI
import dotenv

dotenv.load_dotenv()

class ExecutiveAgency:
    def __init__(self, llm_client):
        self.client = llm_client
        self.registrar = RegistrarBot(self.client)
        self.strategist = ChiefStrategist(self.client)

    def hire(self, role):
        if role == "registrar": return self.registrar
        if role == "strategist": return self.strategist

def get_client():
    # OpenRouter actúa como un proxy compatible con OpenAI
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        default_headers={
            "HTTP-Referer": "https://tu-sitio-o-repo-url.com", # Requerido por OpenRouter
            "X-Title": "Executive Performance Engine"          # Nombre de tu app
        }
    )
    return client

# En src/agents/agency.py
client = get_client()
registrar = RegistrarBot(llm_client=client)
strategist = ChiefStrategist(llm_client=client)