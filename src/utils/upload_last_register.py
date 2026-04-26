import streamlit as st

# 1. Función Modular (en src/utils/state_handlers.py o similar)
def sync_exercise_state(db, ejercicios_validos):
    """Sincroniza el estado basándose en el selector actual."""
    ej_sel = st.session_state.ejercicio_selector
    ultimo = db.get_last_record(ej_sel)
    st.session_state.peso_input = float(ultimo["peso"])
    st.session_state.reps_input = int(ultimo["reps"])

# 2. En tu UI (src/ui/meta_ejercicio.py)
    with st.expander("📝 Registrar Serie (Entrada Directa)", expanded=True):
        # EL SELECTOR VA FUERA DEL FORM PARA SER REACTIVO
        ejercicio_sel = st.selectbox(
            "Selecciona tu ejercicio:",
            options=ejercicios_validos,
            key="ejercicio_selector",
            on_change=lambda: sync_exercise_state(db)
        )

        # Inicialización de seguridad
        if "peso_input" not in st.session_state:
            sync_exercise_state(db)

        # USAMOS COLUMNAS NORMALES (SIN ST.FORM)
        col1, col2, col3 = st.columns(3)
        with col1:
            peso = st.number_input("Peso (kg)", step=0.25, key="peso_input")
        with col2:
            reps = st.number_input("Reps", step=1, key="reps_input")
        with col3:
            duracion = st.number_input("Duración (seg)", min_value=0, step=1)

        # BOTÓN DE ENVÍO MANUAL
        if st.button("🚀 ENVIAR AL COACH", use_container_width=True):
            # Aquí llamas a tu lógica de guardado
            db.save_record(ejercicio_sel, peso, reps, duracion)
            st.success("¡Serie registrada!")