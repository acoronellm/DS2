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
    tipo_operacion VARCHAR(30),
    numero_documento VARCHAR(20),
    fecha_transaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detalle TEXT
);

-- =========================
-- ÍNDICES
-- =========================
CREATE INDEX idx_logs_tipo
ON logs(tipo_operacion);

CREATE INDEX idx_logs_documento
ON logs(numero_documento);

CREATE INDEX idx_logs_fecha
ON logs(fecha_transaccion);

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