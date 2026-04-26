import streamlit as st
from src.database.manager import DatabaseManager
from src.agents.meta_architect import MetaArchitect
from src.utils.model_config import get_openai_client
from src.agents.chief_strategist import ChiefStrategist
from datetime import date
from src.agents.registrar_bot import RegistrarBot
from src.agents.grind_master import GrindMaster
db = DatabaseManager()
import json
import datetime
from src.utils.calendar_handler import CalendarHandler
from src.ui.meta_grind import render_meta_grind
from src.ui.meta_activity import render_pagina_registro
from src.ui.meta_ejercicio import render_gestion_ejercicios # Asegúrate de crear este archivo
from src.agents.iron_architect import IronArchitect
from src.agents.coach_pain import IronCoach

st.title("🛡️ Executive Performance Engine")

tab1, tab2, tab3, tab4 = st.tabs([
    "Registro de Actividad", 
    "Gestión de Metas", 
    "Tactical Scheduler",
    "🏋️ Entrenamiento (Heavy Duty)"
])

# 1. Obtener metas disponibles para el selectbox
metas = db.get_all_metas() # Asumimos que esta función devuelve una lista de diccionarios/tuplas
meta_options = {m['nombre']: m['id'] for m in metas}

agente_arquitecto = MetaArchitect(llm_client=get_openai_client())
registrar_bot = RegistrarBot(llm_client=get_openai_client())
gm = GrindMaster(llm_client=get_openai_client())
iron_architect = IronArchitect(llm_client=get_openai_client())
coach_pain = IronCoach(llm_client=get_openai_client(), db=db)

MODO_MAP = {
    "Corto Plazo (3 días)": 3,
    "Mensual (30 días)": 30
}

if 'calendar_bot' not in st.session_state:
    st.session_state['calendar_bot'] = CalendarHandler()
calendar = st.session_state['calendar_bot']

if 'dialectical_history' not in st.session_state:
    st.session_state['dialectical_history'] = []
    st.session_state['call_count'] = 0

# Función para interactuar con Claude manteniendo el historial
def send_dialectical_message(user_input):
    if st.session_state['call_count'] < 3:
        # Añadir mensaje de usuario al historial
        st.session_state['dialectical_history'].append({"role": "user", "content": user_input})
        
        # Llamar a Claude con todo el historial acumulado
        response = ChiefStrategist.continue_dialogue(st.session_state['dialectical_history'])
        
        # Guardar respuesta
        st.session_state['dialectical_history'].append({"role": "assistant", "content": response})
        st.session_state['call_count'] += 1
        return response
    else:
        return "⚠️ Has alcanzado el límite de 3 interacciones dialécticas para esta auditoría. Abre una nueva auditoría para profundizar más."

with tab1:
    render_pagina_registro(db, st.session_state['calendar_bot'])



with tab2:
    st.header("Gestión de Metas Estratégicas")
    
    # 1. MODO ESTRATÉGICO ASISTIDO (Brian Tracy)
    st.subheader("Establecimiento Asistido")
    # Importante: Asegúrate de inicializar meta_architect antes o inyectarlo
    from src.ui.meta_form import render_meta_chat_interface
    render_meta_chat_interface(agente_arquitecto,db) # Pasa la instancia de tu agente aquí
    
    st.divider()
    
    # 2. MODO MANUAL (Para ajustes rápidos o correcciones)
    with st.expander("➕ Crear Meta Manualmente"):
        with st.form("meta_form", clear_on_submit=True):
            nombre = st.text_input("Nombre de la meta")
            contexto = st.text_area("¿Por qué es importante?")
            prioridad = st.slider("Prioridad (1-10)", 1, 10, 5)
            deadline = st.date_input("Fecha límite")
            
            if st.form_submit_button("Registrar Meta Directa"):
                db.add_meta(nombre, contexto, prioridad, deadline)
                st.success(f"Meta '{nombre}' registrada.")
                st.rerun() # Recargar para ver el cambio inmediato

    # 3. VISUALIZACIÓN DE METAS
    st.divider()
    st.subheader("🎯 Tus Metas Actuales")

    metas = db.get_all_metas()
    if not metas:
        st.info("No tienes metas registradas.")
    else:
        for row in metas:
            meta = dict(row) 
            
            with st.expander(f"🎯 {meta.get('nombre', 'Sin nombre')} (Prioridad: {meta.get('prioridad', 3)})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Declaración:** {meta.get('declaracion', 'No definida')}")
                    st.write(f"**Por qué:** {meta.get('por_que', 'No definido')}")
                with col2:
                    p = meta.get('prioridad', 0)
                    # Barra de progreso visual para la prioridad
                    st.progress(p / 10)
                    st.write(f"**Nivel de Importancia:** {p}/10")
                
                st.divider()
                
                # MOSTRAR MÉTRICAS (NUEVO)
                st.write("**📊 Métricas de Éxito:**")
                metricas_raw = meta.get('metricas_json')
                if metricas_raw:
                    try:
                        metricas = json.loads(metricas_raw)
                        if metricas:
                            for m in metricas:
                                st.markdown(f"- {m}")
                        else:
                            st.info("No se definieron métricas específicas.")
                    except:
                        st.write(metricas_raw)
                
                st.write("")
                st.write("**📝 Plan de Acción:**")
                
                acciones_raw = meta.get('acciones_json')
                if acciones_raw:
                    try:
                        # Intentamos deserializar el JSON
                        acciones = json.loads(acciones_raw)
                        for i, accion in enumerate(acciones, 1):
                            st.write(f"{i}. {accion}")
                    except:
                        st.write(acciones_raw) # Si no es JSON, lo mostramos como texto
                else:
                    st.info("Aún no hay un plan de acción detallado para esta meta.")

                edit_mode = st.toggle("📝 Modo Edición", key=f"edit_mode_{meta['id']}")
        
                if edit_mode:
                    with st.form(key=f"form_edit_{meta['id']}"):
                        # 1. Editar Prioridad
                        new_prio = st.slider("Prioridad", 1, 10, int(meta['prioridad'] or 5))
                        
                        # 2. Editar Métricas (como es JSON, lo mostramos como texto para editar fácil)
                        new_metrics = st.text_area("Métricas de Éxito (JSON o Lista)", value=meta['metricas_json'])
                        
                        # 3. Editar Plan de Acción
                        new_actions = st.text_area("Plan de Acción (JSON o Lista)", value=meta['acciones_json'])
                        
                        if st.form_submit_button("Guardar Cambios"):
                            success = db.update_meta_fields(
                                meta['id'], 
                                new_prio, 
                                new_metrics, 
                                new_actions
                            )
                            if success:
                                st.success("Estrategia actualizada.")
                                st.rerun()
                            else:
                                st.error("Error al guardar.")
                else:
                    # Vista Normal (Lectura)
                    st.write(f"**Prioridad:** {meta['prioridad']}")
                    st.write(f"**Métricas:** {meta['metricas_json']}")
                    st.write(f"**Acciones:** {meta['acciones_json']}")

                confirm_key = f"confirm_delete_{meta['id']}"
        
                if confirm_key not in st.session_state:
                    st.session_state[confirm_key] = False

                if not st.session_state[confirm_key]:
                    # Primer paso: Botón normal
                    if st.button("🗑️ Eliminar Meta", key=f"btn_init_{meta['id']}"):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    # Segundo paso: Alerta de seguridad y botones de decisión
                    st.warning("⚠️ ¿Estás seguro? Esta acción es irreversible.")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🔥 SÍ, BORRAR", key=f"btn_final_{meta['id']}", type="primary"):
                            if db.delete_meta_by_id(meta['id']):
                                st.session_state[confirm_key] = False # Limpiamos estado
                                st.success("Meta eliminada.")
                                st.rerun() #
                    
                    with col2:
                        if st.button("❌ CANCELAR", key=f"btn_cancel_{meta['id']}"):
                            st.session_state[confirm_key] = False
                            st.rerun()

with tab3:
    st.header("⚡ The Grind Master: Tactical Scheduler")
    
    # Delegación total al componente meta_grind
    # Pasamos las instancias necesarias para la autonomía total
    render_meta_grind(db, calendar, gm)

with tab4:
    st.header("⚙️ Configuración de Entrenamiento")
    # Inyectamos la interfaz que definimos anteriormente
    render_gestion_ejercicios(db, calendar, iron_architect, coach_pain)