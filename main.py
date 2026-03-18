import sys
from src.database.manager import DatabaseManager
from src.agents.reviewer import PerformanceReviewer
import os
from dotenv import load_dotenv

# Forzar carga
load_dotenv(verbose=True)

key = os.getenv("OPENROUTER_API_KEY")
print(f"DEBUG: API Key encontrada: {'SÍ' if key else 'NO'}")

def main():
    db = DatabaseManager()
    reviewer = PerformanceReviewer()

    while True:
        print("\n--- SISTEMA DE GESTIÓN DE VICTORIAS ---")
        print("1. Registrar nueva victoria")
        print("2. Solicitar análisis del Agente (Revisión diaria)")
        print("3. Salir")
        
        choice = input("Seleccione una opción: ")

        if choice == '1':
            # Registro manual solicitado
            error = input("¿Qué problema superaste? ")
            solution = input("¿Cómo lo resolviste? ")
            difficulty = input("Dificultad (1-5): ")
            db.add_victory(error, solution, difficulty)
            print("Victoria registrada con éxito.")

        elif choice == '2':
            # Análisis bajo demanda
            victories = db.get_todays_victories()
            if victories:
                print("\nEjecutando autopsia técnica...\n")
                print(reviewer.generate_review(victories))
            else:
                print("No hay victorias para analizar hoy.")
        
        elif choice == '3':
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    main()