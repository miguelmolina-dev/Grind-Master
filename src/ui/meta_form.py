import streamlit as st
import json
import time

if 'memoria_estrategica' not in st.session_state:
    st.session_state['memoria_estrategica'] = "Inicio de la sesión: definiendo visión estratégica."

def es_meta_valida(meta_json):
    # Definimos los campos mínimos para considerar la meta como "analizable"
    campos_criticos = ['nombre_meta', 'declaracion', 'por_que', 'fecha_limite']
    completos = all(meta_json.get(campo) for campo in campos_criticos)
    tiene_acciones = len(meta_json.get('acciones', [])) > 0
    return completos and tiene_acciones

def render_meta_chat_interface(agente_arquitecto, db):
    # 1. Inicialización de estado
    if 'meta_json' not in st.session_state:
        st.session_state['meta_json'] = {
            "nombre_meta": None, 
            "declaracion": None, 
            "fecha_limite": None,
            "por_que": None, 
            "prioridad": 3, # Default intermedio
            "acciones": [],
            "metricas": [] # Nuevo campo
        }
    
    if 'chat_abierto' not in st.session_state:
        st.session_state['chat_abierto'] = False
        st.session_state['meta_historial'] = []
        st.session_state['meta_id_activo'] = None

    # 2. Botón de inicio
    if st.button("🚀 Iniciar Establecimiento de Metas"):
        st.session_state['chat_abierto'] = True
        meta_id = db.add_meta(
            nombre="Nueva Meta en Proceso",
            declaracion="Pendiente",
            por_que="Pendiente",
            deadline=None,
            acciones_json="[]",
            prioridad=3,
            estado_actual="En Proceso",
            metricas_json="[]" # Añadido
        )
        st.session_state['meta_id_activo'] = meta_id
        st.rerun()

    # 3. Interfaz de Chat
    if st.session_state['chat_abierto']:
        st.divider()
        st.subheader("🤖 Mentor Estratégico")

        chat_container = st.container()

        # Mostrar historial visual
        with chat_container:
            for msg in st.session_state['meta_historial']:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        meta = st.session_state.get('meta_json', {})

        if meta.get('nombre_meta') and len(meta.get('acciones', [])) > 0:
            st.divider()
            st.subheader("⚖️ Validación de Prioridad Estratégica")
            
            # Slider de 1 a 10
            prioridad_seleccionada = st.slider(
                "Asigna la prioridad real para el Planificador (1: Baja - 10: Crítica)",
                1, 10, value=st.session_state['meta_json'].get('prioridad', 5)
            )
            
            # Actualizamos el JSON antes de guardar
            st.session_state['meta_json']['prioridad'] = prioridad_seleccionada
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Auditoría del Plan", use_container_width=True):
                    # 1. Definimos el prompt de auditoría
                    prompt_auditoria = "Haz una auditoría técnica de mi plan actual. Evalúa coherencia, realismo y lagunas, y sugiere mejoras concretas."
                    
                    # 2. Lo añadimos al historial para que sea visible
                    st.session_state['meta_historial'].append({"role": "user", "content": prompt_auditoria})
                    
                    # 3. LANZAMOS EL TRIUNVIRATO (Esto es lo que faltaba)
                    with st.status("🧐 El Triunvirato está auditando tu estrategia...", expanded=True) as status:
                        # Reutilizamos la lógica del arquitecto
                        resultado = agente_arquitecto.extraer_y_preguntar(
                            entrada_usuario=prompt_auditoria,
                            snapshot_json=st.session_state['meta_json'],
                            historial_completo=st.session_state['meta_historial'][-4:],
                            memoria_estrategica=st.session_state['memoria_estrategica']
                        )
                        
                        if resultado:
                            # Guardamos la respuesta del mentor
                            st.session_state['meta_historial'].append({
                                "role": "assistant", 
                                "content": resultado.get('texto')
                            })
                            # Actualizamos memoria si es necesario
                            st.session_state['memoria_estrategica'] = resultado.get('memoria')
                            status.update(label="✅ Auditoría completada", state="complete")
                        else:
                            status.update(label="❌ Error en la auditoría", state="error")
                    
                    # 4. Refrescamos para mostrar la respuesta del agente
                    st.rerun()

            with col2:
                # EL BOTÓN SOLO SE ACTIVA SI SE HA INTERACTUADO O CONFIRMADO
                if st.button("🏁 CONSOLIDAR Y GUARDAR", type="primary", use_container_width=True):
                    # Sincronizamos el ID activo con el JSON final
                    db.finalizar_meta_estrategica(
                        st.session_state['meta_id_activo'], 
                        st.session_state['meta_json']
                    )
                    st.balloons()
                    st.session_state['chat_abierto'] = False
                    st.success(f"Meta '{meta['nombre_meta']}' guardada con prioridad {prioridad_seleccionada}")
                    time.sleep(1)
                    st.rerun()

        if prompt := st.chat_input("Hablemos de tu meta..."):
            # Registro inmediato
            st.session_state['meta_historial'].append({"role": "user", "content": prompt})
            # Forzamos el renderizado en el contenedor para que aparezca abajo
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            # --- FILTRADO SEGURO DE HISTORIAL (CASO n=0) ---
            solo_usuario = [m["content"] for m in st.session_state['meta_historial'] if m["role"] == "user"]
            
            solo_usuario_previo = [m["content"] for m in st.session_state['meta_historial'][:-1] if m["role"] == "user"]
            historial_reducido = solo_usuario_previo[-4:] if solo_usuario_previo else []

            # Si es el primer mensaje, el historial reducido es simplemente un aviso de inicio
            if len(solo_usuario) <= 1:
                historial_reducido = ["Inicio de conversación estratégica"]
            else:
                # Tomamos los últimos 4 sin incluir el actual (que va por separado en 'entrada_usuario')
                historial_reducido = solo_usuario[:-1][-4:]

            texto_chat = ""
            max_reintentos = 3
            intento = 0
            
            # Feedback visual de estado
            with st.status("🧠 Analizando estrategia...", expanded=True) as status:
                while intento < max_reintentos:
                    st.write(f"Intento {intento + 1}: Consultando al Triunvirato...")
                    
                    try:
                        resultado = agente_arquitecto.extraer_y_preguntar(
                            entrada_usuario=prompt,
                            snapshot_json=st.session_state['meta_json'],
                            historial_completo=historial_reducido,
                            memoria_estrategica=st.session_state['memoria_estrategica']
                        )

                        if resultado and isinstance(resultado, dict) and 'texto' in resultado:
                            texto_chat = resultado.get('texto')
                            st.session_state['memoria_estrategica'] = resultado.get('memoria', st.session_state['memoria_estrategica'])
                            
                            if resultado.get('aprobado'):
                                st.session_state['meta_json'] = resultado.get('entregable', st.session_state['meta_json'])
                            
                            status.update(label="✅ Análisis completo", state="complete", expanded=False)
                            break
                    except Exception as e:
                        st.error(f"Fallo en intento {intento + 1}: {e}")
                    
                    intento += 1
                    time.sleep(1)

                if not texto_chat:
                    texto_chat = "He tenido un problema al estructurar mi pensamiento. ¿Podrías intentar decirme lo mismo de otra forma?"
                    status.update(label="❌ Error de formato", state="error")

            # Mostrar respuesta del asistente
            st.session_state['meta_historial'].append({"role": "assistant", "content": texto_chat})
            with st.chat_message("assistant"):
                st.markdown(texto_chat)
            st.rerun()

            if es_meta_valida(st.session_state['meta_json']):
                st.divider()
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📊 Auditoría del Plan", use_container_width=True):
                        # EJECUCIÓN INMEDIATA (Lo que faltaba)
                        auditoria_msg = "Realiza una auditoría técnica de mi plan actual."
                        st.session_state['meta_historial'].append({"role": "user", "content": auditoria_msg})
                        
                        # Llamamos al agente aquí mismo
                        with st.status("🧐 Analizando coherencia..."):
                            res = agente_arquitecto.extraer_y_preguntar(
                                entrada_usuario=auditoria_msg,
                                snapshot_json=st.session_state['meta_json'],
                                historial_completo=st.session_state['meta_historial'][-4:],
                                memoria_estrategica=st.session_state['memoria_estrategica']
                            )
                            if res:
                                st.session_state['meta_historial'].append({"role": "assistant", "content": res['texto']})
                        st.rerun() # Forzamos recarga para mostrar la auditoría

                with col2:
                    if st.button("🏁 Consolidar y Finalizar", type="primary", use_container_width=True):
                        # GUARDAR EN DB
                        db.finalizar_meta_estrategica(st.session_state['meta_id_activo'], st.session_state['meta_json'])
                        st.balloons()
                        # RESET DE ESTADOS
                        st.session_state['chat_abierto'] = False
                        st.session_state['meta_historial'] = []
                        st.session_state['meta_id_activo'] = None
                        st.success("🎯 ¡Meta guardada!")
                        time.sleep(1)
                        st.rerun()

                # Lógica de cierre
            if "PLAN COMPLETO" in texto_chat.upper():
                st.balloons()
                db.finalizar_meta_estrategica(st.session_state['meta_id_activo'], st.session_state['meta_json'])
                st.success("🎯 ¡Plan consolidado!")
                if st.button("Finalizar y volver al Dashboard"):
                    st.session_state['chat_abierto'] = False
                    st.rerun()
