# meta_activity.py (o logic/enriquecedor.py)
import streamlit as st

def enriquecer_plan_del_dia(db, agent, calendar_handler):
    """
    Coordina el enriquecimiento de tareas:
    DB -> Agent -> Google Calendar -> DB
    """
    # 1. Obtenemos bloques que NO tengan detalles aún para ahorrar tiempo/tokens
    bloques = db.get_bloques_sin_detalles() # Necesitarás este método en manager.py
    
    if not bloques:
        # Esto ahora solo saldrá si realmente no hay nada pendiente para HOY
        st.info("No hay tareas pendientes de detallar para el día de hoy.")
        return 0

    metas_contexto = db.get_all_metas()
    procesados = 0

    for bloque in bloques:
        # Llamada al LLM para generar el protocolo detallado
        detalle = agent.generar_instrucciones(
            tarea=bloque['tarea'], 
            duracion=bloque['duracion_min'],
            metas=metas_contexto
        )
        
        # Actualizamos Google Calendar
        if bloque['google_event_id']:
            calendar_handler.update_event_description(
                bloque['google_event_id'], 
                detalle
            )
            
        # Actualizamos la DB local
        db.update_detalles_bloque(bloque['id'], detalle)
        procesados += 1
        
    return procesados