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
    fecha TEXT DEFAULT (date('now')),
    hora_inicio TEXT NOT NULL,          -- Formato HH:MM
    duracion_min INTEGER NOT NULL,      -- Para el cálculo de precisión en el calendario
    tarea TEXT NOT NULL,
    tipo TEXT NOT NULL,                 -- Deep Work, Shallow, Rest
    prioridad INTEGER CHECK(prioridad BETWEEN 1 AND 10),
    completado BOOLEAN DEFAULT 0,       -- 0: No hecho, 1: Hecho
    google_event_id TEXT,               -- Para vincularlo con el calendario secundario
    detalles_tacticos TEXT,             -- La descripción detallada generada por el Agente
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

CREATE TABLE IF NOT EXISTS historial_entrenos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ejercicio_id INTEGER,
    fecha TEXT,
    peso_kg REAL,
    repeticiones INTEGER,
    duracion_seg INTEGER, -- Para planchas/isométricos
    rpe INTEGER, -- Esfuerzo percibido (1-10)
    notas_fallo TEXT, -- "Fallo técnico en rep 6"
    FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id)
);

CREATE TABLE IF NOT EXISTS ejercicios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    grupo_muscular TEXT NOT NULL, -- 'espalda_biceps', 'abdominales', 'pecho_triceps', 'piernas_hombros'
    tipo_medicion TEXT DEFAULT 'peso', -- 'peso' o 'tiempo' (para planchas)
    instrucciones_tecnicas TEXT
);

CREATE TABLE IF NOT EXISTS config_rutinas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grupo_muscular TEXT UNIQUE NOT NULL, -- 'espalda_biceps', etc.
    ejercicios_referencia TEXT NOT NULL, -- Lista de ejercicios y series ideal
    notas_estilo TEXT -- Ej: "Enfoque en Heavy Duty, cadencia lenta"
);

CREATE TABLE IF NOT EXISTS sesion_activa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ejercicio_nombre TEXT,
    estatus TEXT DEFAULT 'pendiente', -- 'pendiente', 'completado'
    peso_objetivo REAL,
    reps_objetivo INTEGER
);

CREATE TABLE IF NOT EXISTS registro_entrenamientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ejercicio_nombre TEXT NOT NULL,
    grupo_muscular TEXT NOT NULL,
    peso_real REAL,
    reps_reales INTEGER,
    duracion_seg INTEGER,
    fallo_alcanzado BOOLEAN,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Ahora sí, aplicamos la optimización que te pasé antes
CREATE INDEX IF NOT EXISTS idx_historial_ejercicio 
ON registro_entrenamientos (ejercicio_nombre, fecha DESC);