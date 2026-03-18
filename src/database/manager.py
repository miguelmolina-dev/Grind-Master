import sqlite3
import json
from datetime import datetime, timedelta
import os

class DatabaseManager:
    def __init__(self, db_path='data/engine.db'):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.db_path = db_path
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
        

    def _create_tables(self):
        # Ruta dinámica absoluta para no fallar
        base_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(base_dir, 'schema.sql')
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_script = f.read()
            self.conn.executescript(schema_script)
            self.conn.commit()
        except FileNotFoundError:
            print(f"⚠️ Alerta: No se encontró el esquema en {schema_path}")

    def insertar_log_inicial(self, data, meta_id):
        # Uso de .get() para evitar el KeyError
        query = """INSERT INTO logs (meta_id, categoria, evento, solucion, dificultad, analisis_cognitivo, pregunta_reflexiva) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)"""
        cursor = self.conn.cursor()
        cursor.execute(query, (
            meta_id, 
            data.get('categoria', 'General'), 
            data.get('evento', 'Registro'), 
            data.get('solucion', 'N/A'), 
            data.get('dificultad', 1), # Valor por defecto si falta
            data.get('analisis_cognitivo', ''), 
            data.get('pregunta_reflexiva', '')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def actualizar_log_con_respuesta(self, log_id, respuesta):
        """Cierra el ciclo de registro añadiendo la respuesta humana."""
        query = "UPDATE logs SET respuesta_usuario = ? WHERE id = ?"
        self.conn.execute(query, (respuesta, log_id))
        self.conn.commit()
    
    def add_meta(self, nombre, declaracion, por_que, deadline, acciones_json, prioridad, estado_actual, metricas_json):
        cursor = self.conn.cursor()
        query = """
            INSERT INTO metas (nombre, declaracion, por_que, deadline, acciones_json, prioridad, estado_actual, metricas_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (nombre, declaracion, por_que, deadline, acciones_json, prioridad, estado_actual, metricas_json))
        self.conn.commit()
        return cursor.lastrowid

    def get_all_metas(self):
        # Usamos una nueva conexión o la existente
        conn = sqlite3.connect(self.db_path)
        # ESTA ES LA LÍNEA MÁGICA
        conn.row_factory = sqlite3.Row 
        
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM metas ORDER BY created_at DESC")
            # Al usar Row, fetchall() devuelve objetos accesibles por nombre
            return cursor.fetchall() 
        except sqlite3.Error as e:
            print(f"Error al extraer datos: {e}")
            return []
        finally:
            conn.close()
    
    def get_strategic_report_data(self, days=30):
        """Extrae el contexto completo para la auditoría de Claude."""

        query = """
            SELECT 
                m.nombre as meta, m.contexto as meta_contexto,
                l.evento, l.solucion, l.dificultad, l.analisis_cognitivo, 
                l.pregunta_reflexiva, l.respuesta_usuario
            FROM logs l
            JOIN metas m ON l.meta_id = m.id
            WHERE l.fecha >= date('now', '-' || ? || ' days')
            ORDER BY l.fecha ASC
            """
        return self.conn.execute(query, (days,)).fetchall()

    def guardar_reporte_final(self, titulo, historial_completo, modelo="claude-3.5-sonnet"):
        """
        Serializa el historial de mensajes a formato texto/JSON 
        para persistencia a largo plazo.
        """
        
        contenido = json.dumps(historial_completo)
        query = "INSERT INTO reportes (titulo, contenido_completo, modelo_utilizado) VALUES (?, ?, ?)"
        self.conn.execute(query, (titulo, contenido, modelo))
        self.conn.commit()

    def get_audit_data(self, days):
        """
        Extrae registros de los últimos 'days' días.
        Retorna una lista de tuplas con los datos del log.
        """
        # 1. Calcular fecha de inicio
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 2. Conectar y ejecutar query
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ajusta 'created_at' y 'logs' según los nombres de tu tabla real
        query = """
            SELECT * FROM logs 
            WHERE created_at >= datetime('now', '-' || ? || ' days')
            ORDER BY created_at ASC
            """
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (days,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al extraer datos: {e}")
            return []
        finally:
            conn.close()
    
    def finalizar_meta_estrategica(self, meta_id, entregable_db):
        """
        Consolida la meta en la base de datos con los nuevos campos de prioridad y métricas.
        """
        try:
            cursor = self.conn.cursor()
            
            # --- NORMALIZACIÓN DE DATOS ---
            # El Agente puede devolver 'nombre' o 'nombre_meta'
            nombre = entregable_db.get("nombre_meta") or entregable_db.get("nombre") or "Meta sin nombre"
            
            # El Agente puede devolver 'deadline' o 'fecha_limite'
            deadline = entregable_db.get("fecha_limite") or entregable_db.get("deadline")
            
            # Aseguramos que prioridad sea un entero (1-5)
            try:
                prioridad = int(entregable_db.get("prioridad", 5))
                metricas = json.dumps(entregable_db.get('metricas', []), ensure_ascii=False)
            except (ValueError, TypeError):
                prioridad = 3
            
            # Procesamiento de Listas a JSON Strings
            # Acciones
            acciones = entregable_db.get("acciones") or []
            acciones_json = json.dumps(acciones, ensure_ascii=False)
            
            # Métricas (Nuevo campo)
            metricas = entregable_db.get("metricas") or []
            metricas_json = json.dumps(metricas, ensure_ascii=False)

            query = """
                UPDATE metas 
                SET nombre = ?, 
                    declaracion = ?, 
                    por_que = ?, 
                    deadline = ?, 
                    acciones_json = ?, 
                    metricas_json = ?,
                    prioridad = ?, 
                    estado_actual = 'Activa'
                WHERE id = ?
            """
            
            cursor.execute(query, (
                nombre,
                entregable_db.get("declaracion"),
                entregable_db.get("por_que"),
                deadline,
                acciones_json,
                metricas_json,
                prioridad,
                meta_id
            ))
            
            self.conn.commit()
            print(f"✅ Meta {meta_id} consolidada exitosamente.")
            
        except Exception as e:
            print(f"❌ Error crítico en finalizar_meta_estrategica: {e}")
            self.conn.rollback()

    def save_generated_plan(self, plan_json, google_ids):
        """Guarda el plan y sus bloques. Solo recibe 2 argumentos."""
        try:
            # Insertar en planes_diarios (especificando columnas)
            query_plan = """
                INSERT INTO planes_diarios (analisis_tactico, arenga, status) 
                VALUES (?, ?, ?)
            """
            self.cursor.execute(query_plan, (
                plan_json.get('analisis_tactico', 'Sin análisis'),
                plan_json.get('arenga', '¡A darle!'),
                'pendiente'
            ))
            plan_id = self.cursor.lastrowid

            # Insertar bloques
            cronograma = plan_json.get('plan', [])
            query_bloque = """
                INSERT INTO bloques_trabajo 
                (plan_id, hora_inicio, duracion_min, tarea, tipo, prioridad, google_event_id, completado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            for slot, g_id in zip(cronograma, google_ids):
                # Mapeo flexible para el JSON de la IA
                prioridad = slot.get('prio') or slot.get('prioridad') or 5
                duracion = slot.get('duracion_min') or 60 # Por si la IA olvida el nuevo campo
                
                self.cursor.execute(query_bloque, (
                    plan_id,
                    slot.get('hora'),
                    duracion,
                    slot.get('tarea'),
                    slot.get('tipo', 'Deep Work'),
                    prioridad,
                    g_id,
                    0 # completado = False
                ))
                
            self.conn.commit()
            return plan_id
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Error al guardar plan: {e}")
            return None

    def actualizar_estatus_bloque(db_path, bloque_id, completado):
        """Actualiza el cumplimiento y retorna el ID de Google del evento."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE bloques_trabajo 
                SET completado = ? 
                WHERE id = ?
            ''', (1 if completado else 0, bloque_id))
            
            # Recuperamos el ID de Google para el paso siguiente
            cursor.execute('SELECT google_event_id FROM bloques_trabajo WHERE id = ?', (bloque_id,))
            result = cursor.fetchone()
            conn.commit()
            return result[0] if result else None
        finally:
            conn.close()

    def get_bloques_hoy(self):
        query = """
            SELECT b.* FROM bloques_trabajo b
            JOIN planes_diarios p ON b.plan_id = p.id
            WHERE p.fecha = DATE('now', 'localtime')
            ORDER BY b.hora_inicio ASC
        """
        try:
            self.cursor.execute(query)
            # Convertimos a lista de dicts real
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.OperationalError:
            return []

    def update_block_status(self, bloque_id, completado):
        estado = 1 if completado else 0
        try:
            # 1. Actualizar estatus
            self.cursor.execute("UPDATE bloques_trabajo SET completado = ? WHERE id = ?", (estado, bloque_id))
            
            # 2. Obtener el ID de Google vinculado
            self.cursor.execute("SELECT google_event_id FROM bloques_trabajo WHERE id = ?", (bloque_id,))
            res = self.cursor.fetchone()
            
            self.conn.commit()
            return res['google_event_id'] if res else None
        except Exception as e:
            print(f"❌ Error al actualizar bloque: {e}")
            return None
    
    def _create_tables(self):
        # Obtiene la ruta del directorio donde está manager.py (src/database/)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Como schema.sql está en la misma carpeta que manager.py, solo unimos los nombres
        schema_path = os.path.join(base_dir, 'schema.sql')
        
        try:
            # Usamos utf-8 para evitar el error de decodificación en Windows
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_script = f.read()
            
            # Ejecutamos usando el cursor que ya inicializamos en el __init__
            self.cursor.executescript(schema_script)
            self.conn.commit()
            print("✅ Esquema de base de datos cargado correctamente.")
            
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo en {schema_path}")
        except Exception as e:
            print(f"❌ Error inesperado al crear tablas: {e}")

    def delete_block_by_google_id(self, google_id):
        """Elimina un bloque asegurando coincidencia de string limpia."""
        try:
            # 1. Limpieza extrema del ID
            clean_id = str(google_id).strip()
            
            # 2. Usamos una transacción limpia
            with self.conn: # Esto maneja el commit/rollback automáticamente
                cursor = self.conn.cursor()
                
                # Usamos LIKE con comodines por si hay caracteres invisibles (\n, \r, etc)
                # Pero solo si el ID es lo suficientemente largo para ser único
                cursor.execute(
                    "DELETE FROM bloques_trabajo WHERE google_event_id LIKE ?", 
                    (f"%{clean_id}%",)
                )
                
                filas = cursor.rowcount
                if filas > 0:
                    print(f"✅ DEBUG: ¡Borrado exitoso! Filas eliminadas: {filas}")
                    return True
                else:
                    # Si falla, imprimimos exactamente qué buscamos para comparar
                    print(f"⚠️ DEBUG: No se encontró '{clean_id}' (Len: {len(clean_id)})")
                    return False
                    
        except Exception as e:
            print(f"❌ DEBUG: Error en delete_block_by_google_id: {e}")
            return False