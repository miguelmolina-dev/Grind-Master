# test_interfaz_real.py
from src.database.manager import DatabaseManager
from src.agents.agency import ExecutiveAgency, get_client

# 1. Probar conexión DB
db = DatabaseManager()
datos = db.get_audit_data(days=3)
print(f"✅ Se extrajeron {len(datos)} registros para auditoría corta.")

# 2. Probar agencia y estrategia
client = get_client()
agency = ExecutiveAgency(client)
resultado = agency.strategist.conduct_audit(datos, mode="short_term")

print("\n--- Resultado de la Auditoría (Prueba) ---")
print(resultado)