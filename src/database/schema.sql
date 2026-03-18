-- Metas de alto nivel (La Visión)
CREATE TABLE IF NOT EXISTS metas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    declaracion TEXT,
    por_que TEXT,
    deadline DATE,
    acciones_json TEXT DEFAULT '[]',
    metricas_json TEXT DEFAULT '[]',
    prioridad INTEGER DEFAULT NULL, -- Cambiado a NULL para forzar la asignación
    estado_actual TEXT DEFAULT 'En Proceso',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Logs Diarios (La Ejecución)
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    meta_id INTEGER,
    categoria TEXT,
    evento TEXT,
    solucion TEXT,
    dificultad INTEGER,
    pregunta_reflexiva TEXT,
    respuesta_usuario TEXT,
    analisis_cognitivo TEXT,
    FOREIGN KEY (meta_id) REFERENCES metas(id)
);

-- Reportes (La Memoria Estratégica)
CREATE TABLE IF NOT EXISTS reportes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    titulo TEXT,
    contenido_completo TEXT, -- Aquí guardaremos el JSON del historial de chat
    modelo_utilizado TEXT
);

-- 1. Tabla de Planes Diarios (La Estrategia de Mando)
CREATE TABLE IF NOT EXISTS planes_diarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE DEFAULT (DATE('now', 'localtime')),
    analisis_tactico TEXT,
    arenga TEXT,
    status TEXT CHECK(status IN ('pendiente', 'completado', 'fallido')) DEFAULT 'pendiente',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Bloques de Trabajo (La Ejecución Táctica)
CREATE TABLE IF NOT EXISTS bloques_trabajo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER,
    hora_inicio TEXT NOT NULL,         -- Formato HH:MM
    duracion_min INTEGER NOT NULL,     -- Para el cálculo de precisión en el calendario
    tarea TEXT NOT NULL,
    tipo TEXT NOT NULL,                -- Deep Work, Shallow, Rest
    prioridad INTEGER CHECK(prioridad BETWEEN 1 AND 10),
    completado BOOLEAN DEFAULT 0,      -- 0: No hecho, 1: Hecho (se marca en Pag 1)
    google_event_id TEXT,              -- Para vincularlo con el calendario secundario
    FOREIGN KEY (plan_id) REFERENCES planes_diarios(id) ON DELETE CASCADE
);

-- 3. Tabla de Métricas de Rendimiento (El Feedback Loop)
CREATE TABLE IF NOT EXISTS metricas_rendimiento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE UNIQUE NOT NULL,
    eficiencia_dw REAL,                -- % de bloques Deep Work completados
    total_minutos_productivos INTEGER,
    foco_dominante TEXT,               -- Basado en las etiquetas (TOEFL, IA, Math)
    observaciones_comandante TEXT,     -- Resumen de la IA sobre tu fatiga
    FOREIGN KEY (fecha) REFERENCES planes_diarios(fecha)
);

-- Índices para optimizar las consultas del Agente
CREATE INDEX IF NOT EXISTS idx_bloques_fecha ON bloques_trabajo(plan_id);
CREATE INDEX IF NOT EXISTS idx_planes_fecha ON planes_diarios(fecha);