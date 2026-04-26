import json
from src.agents.prompts import IRON_ARCHITECT_PROMPT, REFERENCIA_RUTINAS
import datetime
from src.utils.model_config import DEFAULT_MODEL

class IronArchitect:
    def __init__(self, llm_client):
        self.client = llm_client
        self.model = DEFAULT_MODEL

    def planificar_rutina(self, tipo_rutina, historial_previo, guia_maestra):
        """
        tipo_rutina: str (ej. 'espalda_biceps')
        historial_previo: list of dicts (los últimos 3 registros por ejercicio)
        """

        rutina_guia = REFERENCIA_RUTINAS.get(tipo_rutina, "Sin referencia")
        prompt_usuario = f"""
        ESTILO DE ENTRENAMIENTO HOY: {tipo_rutina}
        
        GUÍA MAESTRA (Lo que el usuario prefiere hacer):
        {guia_maestra['ejercicios_referencia']}
        NOTAS DE ESTILO: {guia_maestra['notas_estilo']}
        
        HISTORIAL REAL (Últimos 3 registros):
        {json.dumps(historial_previo, indent=2)}
        
        TAREA: Diseña la sesión de hoy superando los pesos/reps del historial, 
        siguiendo estrictamente los ejercicios de la GUÍA MAESTRA.
        """

        # Usamos la sintaxis correcta del cliente que tienes en app.py
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": IRON_ARCHITECT_PROMPT},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.2 # Baja temperatura para mayor precisión matemática
        )
        return response.choices[0].message.content

    def obtener_grupo_desde_bloques(self, db):
        """
        Busca en la base de datos local los bloques de trabajo de hoy.
        """
        hoy = datetime.date.today().isoformat()
        # Consultamos los bloques que tú mismo registraste
        query = "SELECT tarea FROM bloques_trabajo WHERE fecha = ?"
        bloques = db.execute_query(query, (hoy,))
        
        for b in bloques:
            tarea = b['tarea'].lower()
            # Reutilizamos tu lógica de mapeo
            if "pecho" in tarea or "triceps" in tarea:
                return "pecho_triceps"
            if "espalda" in tarea or "biceps" in tarea:
                return "espalda_biceps"
            if "pierna" in tarea or "hombro" in tarea:
                return "piernas_hombros"
            if "abdomen" in tarea or "abdominales" in tarea:
                return "abdominales"
                
        return None
    
    def obtener_grupo_desde_evento(self, nombre_evento):
        """
        Normaliza el nombre del evento del calendario a las categorías de la DB.
        """
        if not nombre_evento:
            return None
            
        evento = nombre_evento.lower()
        if "pecho" in evento or "triceps" in evento or "tríceps" in evento:
            return "pecho_triceps"
        if "espalda" in evento or "biceps" in evento or "bíceps" in evento:
            return "espalda_biceps"
        if "pierna" in evento or "hombro" in evento:
            return "piernas_hombros"
        if "abdomen" in evento or "abdominales" in evento:
            return "abdominales"
        return None
