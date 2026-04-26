import os
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from src.utils.model_config import get_langchain_llm

load_dotenv()

class PerformanceReviewer:
    def __init__(self):
        # Configuración para OpenRouter a través de model_config
        self.llm = get_langchain_llm(temperature=0.2)

    def generate_review(self, victories):
        if not victories:
            return "No se registraron victorias hoy. ¡Recuerda que cada pequeño paso cuenta!"

        # Convertimos las victorias a texto plano para el prompt
        context = "\n".join([
            f"- Problema: {v['error']} | Solución: {v['solution']} | Dificultad: {v['difficulty']}/5"
            for v in victories
        ])

        prompt = ChatPromptTemplate.from_template("""
        Eres el "System Architect" del usuario. Tu misión es maximizar su tasa de resolución y reducir la fricción técnica.
        Analiza las siguientes victorias del día con una mirada crítica y constructiva:

        {context}

        Responde bajo estos pilares estrictos:

        1. **Autopsia de Eficiencia (Hard Metrics)**:
            - ¿Qué técnica fue ineficiente? Identifica si hubo una ruta más corta que el usuario ignoró.
            - Si un error se repite, califícalo como 'Deuda Técnica' y exige una solución automatizada para mañana.

        2. **Análisis de Fricción Cognitiva**:
            - Analiza la brecha entre la dificultad reportada y la complejidad real. ¿Está el usuario subestimando su capacidad o sobrecomplicando soluciones?

        3. **Arquitectura de Mejora (Actionable Items)**:
           - Proporciona UNA instrucción técnica concreta para evitar que este tipo de errores vuelva a ocurrir (ej: 'Implementa un script de validación', 'Refactoriza la clase X').

        4. **Veredicto de Ejecutor**:
           - Cierra con una sentencia que redefina la percepción de la jornada. Olvida los ánimos superficiales; enfócate en la acumulación de maestría.

        Sé brutalmente honesto y extremadamente profesional. No busques consuelo, busca optimización.
        """)
        
        chain = prompt | self.llm
        response = chain.invoke({"context": context})
        return response.content