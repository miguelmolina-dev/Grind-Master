import streamlit as st

def render_editor_config_rutinas(db):
    """
    Renderiza el editor para las Guías Maestras de entrenamiento.
    """
    st.markdown("#### ⚙️ Configuración de Guías Maestras")
    
    grupos = ["espalda_biceps", "pecho_triceps", "piernas_hombros", "abdominales"]
    seleccion = st.selectbox("Selecciona el grupo a editar:", grupos, key="select_guia_maestra")
    
    # Obtener configuración actual de la DB
    config = db.execute_query_dict("SELECT * FROM config_rutinas WHERE grupo_muscular = ?", (seleccion,))
    
    current_ejercicios = config[0]['ejercicios_referencia'] if config else ""
    current_notas = config[0]['notas_estilo'] if config else ""

    with st.form(f"form_master_{seleccion}", clear_on_submit=False):
        nuevos_ejercicios = st.text_area(
            "Ejercicios de Referencia (separados por coma):", 
            value=current_ejercicios,
            help="Ej: Press Banca, Aperturas, Fondos"
        )
        nuevas_notas = st.text_area(
            "Notas de Estilo/Metodología:", 
            value=current_notas,
            placeholder="Ej: Cadencia 4-0-2-1, enfoque en fallo muscular Mike Mentzer..."
        )
        
        if st.form_submit_button("Actualizar Guía Maestra", use_container_width=True):
            query = """
                INSERT INTO config_rutinas (grupo_muscular, ejercicios_referencia, notas_estilo)
                VALUES (?, ?, ?)
                ON CONFLICT(grupo_muscular) DO UPDATE SET 
                    ejercicios_referencia=excluded.ejercicios_referencia,
                    notas_estilo=excluded.notas_estilo
            """
            db.execute_action(query, (seleccion, nuevos_ejercicios, nuevas_notas))
            st.success(f"✅ Guía de {seleccion.replace('_', ' ').title()} actualizada correctamente.")

def render_formulario_nuevo_ejercicio(db):
    """
    Renderiza el formulario para añadir ejercicios individuales a la biblioteca.
    """
    st.markdown("#### ➕ Registrar Nuevo Ejercicio")
    
    with st.form("nuevo_ejercicio_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del Ejercicio", placeholder="Ej: Remo con Barra")
            grupo = st.selectbox("Categoría Principal", [
                "Espalda", "Biceps", "Pecho", "Triceps", "Piernas", "Hombros", "Abdominales"
            ])
        with col2:
            tipo_medicion = st.radio("Tipo de Progresión", ["peso", "tiempo"], horizontal=True)
            instrucciones = st.text_area("Instrucciones Técnicas", placeholder="Mantener espalda neutra, rango completo...")
        
        if st.form_submit_button("Guardar en Biblioteca", use_container_width=True):
            if nombre:
                # Normalizamos el grupo para la base de datos
                db.insert_ejercicio(nombre, grupo, tipo_medicion, instrucciones)
                st.success(f"✨ '{nombre}' añadido a la biblioteca de {grupo}.")
            else:
                st.error("⚠️ El nombre del ejercicio es obligatorio.")