-- =========================
-- TABLA PRINCIPAL
-- =========================
CREATE TABLE personas_registradas (
    numero_documento VARCHAR(20) PRIMARY KEY,
    tipo_documento_identidad VARCHAR(10),
    primer_nombre VARCHAR(50),
    segundo_nombre VARCHAR(50),
    apellidos VARCHAR(100),
    fecha_nacimiento DATE,
    genero_persona VARCHAR(25),
    correo_electronico VARCHAR(100),
    numero_celular VARCHAR(20),
    url_foto_perfil TEXT,
    rol_usuario VARCHAR(20)
);

-- =========================
-- VISTA PARA IA / CONSULTAS
-- =========================
CREATE VIEW vista_personas_n8n AS
SELECT
    numero_documento AS id_persona,
    tipo_documento_identidad,
    primer_nombre,
    segundo_nombre,
    apellidos,
    fecha_nacimiento,

    EXTRACT(YEAR FROM AGE(fecha_nacimiento)) AS edad,

    TRIM(TO_CHAR(fecha_nacimiento, 'TMDay')) AS dia_semana_nacimiento,

    EXTRACT(DAY FROM fecha_nacimiento) AS dia_nacimiento,
    EXTRACT(MONTH FROM fecha_nacimiento) AS mes_nacimiento,
    EXTRACT(YEAR FROM fecha_nacimiento) AS ano_nacimiento,

    LOWER(TRIM(TO_CHAR(fecha_nacimiento, 'TMMonth'))) AS nombre_mes,

    genero_persona,
    correo_electronico,
    numero_celular,
    url_foto_perfil,
    rol_usuario
FROM personas_registradas;

-- =========================
-- TABLA DE LOGS
-- =========================
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    tipo_operacion VARCHAR(30) NOT NULL,
    numero_documento VARCHAR(20) NOT NULL,
    fecha_transaccion DATE DEFAULT CURRENT_DATE,
    detalle TEXT
);

-- =========================
-- TABLA HISTORIAL N8N
-- =========================
CREATE TABLE n8n (
    id SERIAL PRIMARY KEY,
    numero_documento VARCHAR(20) NOT NULL,
    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- ÍNDICES
-- =========================

-- Para búsquedas por tipo + documento
CREATE INDEX idx_logs_tipo_documento 
ON logs(tipo_operacion, numero_documento);

-- Para búsquedas por fecha de transacción
CREATE INDEX idx_logs_fecha
ON logs(fecha_transaccion);

INSERT INTO logs (tipo_operacion, numero_documento, fecha_transaccion, detalle) VALUES 
('CREATE', '777', CURRENT_DATE, 'Se creó la persona con número de documento 777.');

-- =========================
-- DATO DE PRUEBA
-- =========================
INSERT INTO personas_registradas (
    numero_documento,
    tipo_documento_identidad,
    primer_nombre,
    segundo_nombre,
    apellidos,
    fecha_nacimiento,
    genero_persona,
    correo_electronico,
    numero_celular,
    url_foto_perfil,
    rol_usuario
) VALUES (
    '777',
    'CC',
    'Simon',
    NULL,
    'Giraldo',
    '2004-01-01',
    'Masculino',
    'yop@gmail.com',
    '3000000000',
    '777.jpg',
    'admin'
);

