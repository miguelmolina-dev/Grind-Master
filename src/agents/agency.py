# src/agents/agency.py
from src.agents.registrar_bot import RegistrarBot
from src.agents.chief_strategist import ChiefStrategist
import os
from src.utils.model_config import get_openai_client
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

# En src/agents/agency.py
client = get_openai_client()
registrar = RegistrarBot(llm_client=client)
strategist = ChiefStrategist(llm_client=client)