import os
from openai import OpenAI
from langchain_openai import ChatOpenAI
import dotenv

dotenv.load_dotenv()

DEFAULT_MODEL = "google/gemini-2.0-flash-001"

def get_openai_client():
    """Returns a standard OpenAI client configured for OpenRouter."""
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        default_headers={
            "HTTP-Referer": "https://tu-sitio-o-repo-url.com", # Requerido por OpenRouter
            "X-Title": "Executive Performance Engine"          # Nombre de tu app
        }
    )

def get_langchain_llm(temperature=0.2):
    """Returns a LangChain ChatOpenAI client configured for OpenRouter."""
    return ChatOpenAI(
        model=DEFAULT_MODEL,
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=temperature
    )
