import streamlit as st
import json

def render_meta_grind(db, calendar, gm_agente):
    """Interfaz: Expander Global -> Tabs por Meta -> Cronograma."""
    
    # --- SECCIÓN 1: EL CONTENEDOR GLOBAL (EXPANDER) ---
    # Esto permite "apagar" toda la sección estratégica para enfocarse en el horario
    with st.expander("🎯 PANEL DE CONTROL ESTRATÉGICO", expanded=True):
        
        metas_activas = [dict(m) for m in db.get_all_metas() if m['estado_actual'] == 'Activa']
        
        if not metas_activas:
            st.info("No hay metas activas registradas.")
        else:
            # --- SUB-CONTENEDOR: PESTAÑAS DINÁMICAS ---
            # Aquí el usuario cambia de meta para ver sus métricas y acciones
            nombres_metas = [m['nombre'] for m in metas_activas]
            tabs_metas = st.tabs(nombres_metas)
            
            for i, meta in enumerate(metas_activas):
                with tabs_metas[i]:
                    st.write(f"### 🚀 {meta['nombre']}")
                    
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.markdown("#### 📊 Métricas")
                        metricas_raw = meta.get('metricas_json')
                        if metricas_raw:
                            try:
                                metricas = json.loads(metricas_raw)
                                for m in metricas: st.markdown(f"*{m}*")
                            except: st.write(metricas_raw)
                    
                    with c2:
                        st.markdown("#### 📝 Plan de Acción")
                        acciones_raw = meta.get('acciones_json')
                        if acciones_raw:
                            try:
                                acciones = json.loads(acciones_raw)
                                for acc in acciones: st.markdown(f"- [ ] {acc}")
                            except: st.write(acciones_raw)
    
    st.write("") # Espaciado estético

    # --- SECCIÓN 2: CONTROL DE GENERACIÓN ---
    if 'ped_actual' not in st.session_state:
        st.info("El Comandante espera órdenes para procesar el día.")
        if st.button("🔥 INICIAR ANÁLISIS TÁCTICO", use_container_width=True):
            with st.status("The Grind Master sincronizando...", expanded=True) as status:
                slots_ocupados = calendar.get_today_busy_blocks()
                horas_libres = calendar.get_available_deepwork_slots()
                resultado = gm_agente.generar_plan(
                    metas=metas_activas,
                    horas_dw=horas_libres,
                    restricciones={
                        "bloques_ocupados": slots_ocupados,
                        "horas_reales": horas_libres} 
                )
                st.session_state['ped_actual'] = resultado
                status.update(label="✅ Plan Generado", state="complete")
            st.rerun()

    else:
        # --- SECCIÓN 3: PROTOCOLO DE EJECUCIÓN HORA POR HORA ---
        plan = st.session_state['ped_actual']
        st.success(f"💬 **{plan.get('mensaje_comandante') or plan.get('arenga')}**")
        
        st.subheader("📅 Protocolo de Ejecución")
        
        cronograma = plan.get('plan') or plan.get('plan_detallado') or []

        for slot in cronograma:
            hora = slot.get('hora', '--:--')
            # Extraemos la duración; si no viene en el JSON, ponemos 60 por defecto
            duracion = slot.get('duracion_min', 60)
            tarea = slot.get('tarea') or slot.get('actividad') or "Bloque de Trabajo"
            prio = slot.get('prio', 'P?')
            tipo = slot.get('tipo', 'Deep Work')
            
            # Asignación de emojis según el tipo o palabras clave (TOEFL focus)
            emoji = "🧠" if "Deep" in tipo else "⚙️"
            if "Writing" in tarea: emoji = "🧠"
            elif "Listening" in tarea: emoji = "🎧"
            elif "Speaking" in tarea: emoji = "🗣️"
            elif "Reading" in tarea: emoji = "📖"
            elif "Almuerzo" in tarea or "Descanso" in tarea: emoji = "🍱"

            # Renderizado con la duración visible
            st.markdown(f"### {hora} | {emoji} {tarea}")
            st.caption(f"⏱️ **Duración:** {duracion} min | 🎯 **Prioridad:** P{prio} | 🏷️ **Tipo:** {tipo}")
            st.write("---") # Separador para limpieza visual

        # Footer con Análisis y Botones
        with st.expander("🔬 Análisis del Comandante"):
            st.write(plan.get('analisis_tactico', "Optimización finalizada."))

        c_re, c_sync = st.columns(2)
        if c_re.button("🔄 Re-planificar", use_container_width=True):
            del st.session_state['ped_actual']
            st.rerun()
        if c_sync.button("🗓️ Sincronizar Calendario", type="primary", use_container_width=True):
            with st.spinner("Escribiendo en Google Calendar y Base de Datos..."):
                # 1. Recuperamos el plan actual de la sesión
                plan_a_ejecutar = st.session_state['ped_actual']
                
                # 2. Operación en Google Calendar
                # Nota: push_plan_to_calendar debería devolver una lista de IDs de eventos
                event_ids = calendar.push_plan_to_calendar(plan_a_ejecutar)
                
                if event_ids:
                    # 3. Persistencia en SQLite (Solo si la subida fue exitosa)
                    # Pasamos los IDs de Google para que queden vinculados en bloques_trabajo
                    plan_id = db.save_generated_plan(
                        plan_json=plan_a_ejecutar,
                        google_ids=event_ids
                    )
                    
                    if plan_id:
                        st.success(f"✅ ¡Misión cargada! Plan #{plan_id} activo y {len(event_ids)} eventos sincronizados.")
                        st.balloons()
                    else:
                        st.warning("⚠️ Eventos sincronizados, pero hubo un error al guardar en la DB local.")
                else:
                    st.error("❌ No se pudieron sincronizar los eventos. Revisa la consola.")