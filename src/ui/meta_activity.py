import streamlit as st
import datetime
from googleapiclient.errors import HttpError
from src.utils.add_description import enriquecer_plan_del_dia
from src.agents.agency import get_client # Aquí debes pasar tu instancia de modelo (Gemini o LangChain)
from src.agents.tactical_agent import TacticalPrecisionAgent

agent_tactico = TacticalPrecisionAgent(llm_client=get_client())

def render_pagina_registro(db, calendar_handler):
    st.header("🚀 Registro de Ejecución Diaria")

    # 1. Obtener el plan activo de hoy desde la DB
    # Buscamos el plan más reciente marcado como 'pendiente' o del día de hoy
    bloques = db.get_bloques_hoy()
    
    if not bloques:
        st.info("No hay un plan activo sincronizado. Ve a 'Tactical Scheduler' para generar uno.")
        return

    ids_para_eliminar_db = []
    bloques_eliminados = 0
    
    # Solo verificamos si hay bloques con ID de Google
    for bloque in bloques:
        g_id = bloque.get('google_event_id')
        # PRINT DE CONTROL
        print(f"DEBUG UI: Verificando bloque '{bloque['tarea']}' con Google ID: {g_id}")
        if g_id:
            print(f"DEBUG: Tarea: {bloque['tarea']} | ID_DB: {g_id} | Longitud: {len(g_id)}")
            try:
                response = calendar_handler.service.events().get(
                    calendarId=calendar_handler.grind_calendar_id,
                    eventId=g_id
                ).execute()
                
                # DEBUG: Si llega aquí, es que el evento EXISTE.
                status = response.get('status')
                print(f"DEBUG: Evento '{bloque['tarea']}' existe en Google. Status: {status}")
                
                # Si Google lo marca como 'cancelled' (a veces no da 404, solo cambia status)
                if status == 'cancelled':
                    print(f"DEBUG: Detectado como cancelado. Borrando de DB...")
                    db.delete_block_by_google_id(g_id)
                    bloques_eliminados += 1

            except HttpError as e:
                print(f"DEBUG: ¡ERROR CAPTURADO! Código: {e.resp.status}")
                if e.resp.status == 404:
                    db.delete_block_by_google_id(g_id)
                    bloques_eliminados += 1
    if bloques_eliminados > 0:
        st.toast(f"🧹 Sincronizado: {bloques_eliminados} eventos eliminados por no existir en Google Calendar.")
        st.rerun() # Esto recargará la página con los nuevos datos de la DB después de la limpieza

    # --- SECCIÓN DE MÉTRICAS DINÁMICAS ---
    total_bloques = len(bloques)
    completados = sum(1 for b in bloques if b['completado'])
    eficiencia = (completados / total_bloques) * 100 if total_bloques > 0 else 0

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Progreso del Día", f"{completados}/{total_bloques}", f"{eficiencia:.1f}%")
    
    # Nivel de Exigencia (Dinámico)
    # Si la eficiencia es baja y ya pasó más de la mitad de la jornada
    exigencia = "ALTA" if eficiencia > 70 else "REDUCIDA (Ajuste sugerido)"
    col_m2.metric("Estado de Energía", exigencia)
    
    # 2. RENDERIZADO DE BLOQUES CON MARCADO REAL-TIME
    st.write("---")
    for bloque in bloques:
        col1, col2 = st.columns([0.8, 0.2])
        
        with col1:
            st.write(f"**{bloque['hora_inicio']}** | {bloque['tarea']} (P{bloque['prioridad']})")
        
        with col2:
            check_key = f"check_{bloque['id']}"
            # Nota: usamos bloque['completado'] porque viene de la DB
            marcado = st.checkbox("Hecho", value=bool(bloque['completado']), key=check_key)
            
            # Si el usuario hace clic, actualizamos
            if marcado != bool(bloque['completado']):
                g_id = db.update_block_status(bloque['id'], marcado)
                
                if g_id:
                    # Sincronización con Google Calendar
                    nuevo_color = '10' if marcado else '5'
                    try:
                        calendar_handler.service.events().patch(
                            calendarId=calendar_handler.grind_calendar_id,
                            eventId=g_id,
                            body={'colorId': nuevo_color}
                        ).execute()
                        st.toast(f"Actualizado: {bloque['tarea']}")
                    except Exception as e:
                        st.error(f"Error sincronizando color: {e}")
                
                st.rerun()

    # 3. ACCIÓN DE CIERRE (Métrica de Exigencia)
    if eficiencia < 50 and datetime.datetime.now().hour > 14:
        st.warning("⚠️ El rendimiento está por debajo del 50%. ¿Deseas aplicar un 'Ajuste de Emergencia' al resto de la tarde?")
        if st.button("📉 Re-ajustar Carga Cognitiva"):
            # Aquí llamaríamos a una función que reduzca la prioridad de los bloques restantes
            st.session_state['replan_emergency'] = True
            st.info("Solicitando al Comandante una ruta de escape táctica...")

    # En tu archivo de UI (ej: app.py o meta_activity.py en la parte de render)

    if st.button("🪄 Enriquecer Tareas con IA", help="Genera protocolos detallados para cada bloque"):
        with st.spinner("El Arquitecto Táctico está diseñando tu día..."):
            num = enriquecer_plan_del_dia(db, agent_tactico, calendar_handler)
            if num > 0:
                st.success(f"¡Listo! {num} tareas ahora tienen protocolos en tu Google Calendar.")
                st.rerun()
            else:
                st.info("Todas las tareas ya están detalladas.")