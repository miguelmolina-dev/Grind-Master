import streamlit as st
from src.utils.ui_components import render_editor_config_rutinas, render_formulario_nuevo_ejercicio
import tempfile
import os
import base64
from src.utils.autoplay_audio import autoplay_audio
from src.utils.upload_last_register import sync_exercise_state

MAPEO_RUTINAS = {
    "pecho_triceps": ["Pecho", "Triceps"],
    "espalda_biceps": ["Biceps", "Espalda"], # Nota las mayúsculas y la 's'
    "pierna_hombros": ["Pierna","Hombros"],
    "abdominales": ["Abdominales"]
}

def render_gestion_ejercicios(db, calendar, iron_architect, coach):
    st.title("⚡ Iron Intelligence Hub")
    todos_los_ejercicios = db.get_all_exercises()
    
    # --- SECCIÓN 1: ESTADO ACTUAL (Detección Inteligente) ---
    with st.container(border=True):
        col_status, col_action = st.columns([2, 1])
        
        with col_status:
            st.subheader("🕵️ Detección de Bloques")
            # Prioridad 1: Bloques internos de la DB
            grupo_toca = iron_architect.obtener_grupo_desde_bloques(db)

            # 2. Si no hay bloques, intentar por calendario
            if not grupo_toca:
                evento_cal = calendar.get_next_event()
                if evento_cal and 'summary' in evento_cal:
                    grupo_toca = iron_architect.obtener_grupo_desde_evento(evento_cal['summary'])
                    if grupo_toca:
                        st.info(f"**Calendario:** {evento_cal.get('summary')} ➔ {grupo_toca}")
                    else:
                        st.warning("Evento detectado, pero no coincide con rutinas.")
                else:
                    st.error("No se detectaron bloques de entrenamiento hoy.")

        with col_action:
            st.subheader("🎯 Confirmación")
            opciones = ["Seleccionar...", "pecho_triceps", "espalda_biceps", "piernas_hombros", "abdominales"]
            idx = opciones.index(grupo_toca) if grupo_toca in opciones else 0
            grupo_toca = st.selectbox("Sesión a ejecutar:", opciones, index=idx)

    # --- SECCIÓN 2: PLAN DE ATAQUE (Agente Iron Architect) ---
    if grupo_toca != "Seleccionar...":
        st.divider()
        col_plan, col_guia = st.columns([3, 2])
        
        with col_plan:
            if st.button("🚀 GENERAR PLAN DE ATAQUE", use_container_width=True, type="primary"):
                with st.spinner("Consultando registros históricos..."):
                    historial = db.get_historial_para_agente(grupo_toca)
                    guia_maestra = db.get_guia_maestra(grupo_toca)
                    
                    # Llamada al agente
                    plan = iron_architect.planificar_rutina(grupo_toca, historial, guia_maestra)
                    
                    st.markdown("### 📋 Instrucciones del Iron Architect")
                    st.info(plan)
        
        with col_guia:
            st.markdown("### 🏛️ Guía Maestra")
            guia = db.get_guia_maestra(grupo_toca)
            st.caption(f"**Ejercicios:** {guia['ejercicios_referencia']}")
            st.caption(f"**Notas:** {guia['notas_estilo']}")

        # Dentro de render_gestion_ejercicios, tras generar el plan

        if grupo_toca != "Seleccionar...":
            st.divider()
            clave = grupo_toca.lower().strip()
            musculos_a_buscar = MAPEO_RUTINAS.get(clave, [grupo_toca])
            ejercicios_validos = db.get_exercises_by_muscles(musculos_a_buscar)
            # --- NUEVO FORMULARIO DE ENTRADA RÁPIDA ---

            with st.expander("📝 Registrar Serie (Entrada Directa)", expanded=True):
                with st.form("registro_directo", clear_on_submit=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        ejercicio_sel = st.selectbox(
                            "Selecciona tu ejercicio:",
                            options=ejercicios_validos,
                            key="ejercicio_selector",
                            on_change=lambda: sync_exercise_state(db, st.session_state.ejercicio_selector)
                        )
                    with col2:
                        peso = st.number_input("Peso (kg)", step=0.25, key="peso_input")
                    with col3:
                        reps = st.number_input("Reps", step=1, key="reps_input")
                    
                    col4, col5 = st.columns(2)
                    with col4:
                        duracion = st.number_input("Duración (seg)", min_value=0, step=1)
                    with col5:
                        fallo = st.checkbox("¿Llegaste al fallo?")

                    if st.form_submit_button("⚡ ENVIAR AL COACH", use_container_width=True):
                        # Empaquetamos los datos para el agente
                        datos_serie = {
                            "ejercicio": ejercicio_sel,
                            "peso": peso,
                            "reps": reps,
                            "duracion": duracion,
                            "fallo": fallo
                        }
                        
                        with st.spinner("Coach Pain analizando..."):
                            feedback = coach.procesar_serie_directa(datos_serie, grupo_toca)
                            st.success(feedback)
                            
                            # REPRODUCCIÓN EN NAVEGADOR
                            audio_path = coach.generar_voz_local(feedback)
                            with open(audio_path, "rb") as audio_file:
                                audio_bytes = audio_file.read()
                            
                            # Autoplay para que suene de inmediato
                            audio_path = coach.generar_voz_local(feedback)
                            if audio_path and os.path.exists(audio_path):
                                autoplay_audio(audio_path)

    # --- SECCIÓN 3: BIBLIOTECA Y CONFIGURACIÓN ---
    st.divider()
    tab_lib, tab_config, tab_add = st.tabs(["📚 Biblioteca", "⚙️ Configurar Rutinas", "➕ Añadir Ejercicio"])

    with tab_lib:
        filtro = st.multiselect("Filtrar Grupos", ["Espalda", "Biceps", "Pecho", "Triceps", "Piernas", "Hombros", "Abdominales"])
        query = "SELECT nombre, grupo_muscular, tipo_medicion FROM ejercicios"
        if filtro:
            placeholders = ', '.join(['?'] * len(filtro))
            ejercicios = db.execute_query(f"{query} WHERE grupo_muscular IN ({placeholders})", tuple(filtro))
        else:
            ejercicios = db.execute_query(query)
        st.dataframe(ejercicios, use_container_width=True)

    with tab_config:
        render_editor_config_rutinas(db) # Función auxiliar para limpiar el código

    with tab_add:
        render_formulario_nuevo_ejercicio(db)