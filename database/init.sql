CREATE TABLE personas1 (
    documento VARCHAR(20) PRIMARY KEY,
    tipo_documento VARCHAR(10),
    primer_nombre VARCHAR(50),
    segundo_nombre VARCHAR(50),
    apellidos VARCHAR(100),
    fecha_nacimiento DATE,
    genero VARCHAR(25),
    correo VARCHAR(100),
    celular VARCHAR(20),
    foto_url TEXT,
    rol VARCHAR(20)
);


CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    tipo_operacion VARCHAR(30),
    documento VARCHAR(15),
    fecha_transaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detalle TEXT
);


CREATE INDEX idx_logs_tipo
ON logs(tipo_operacion);

CREATE INDEX idx_logs_documento
ON logs(documento);

CREATE INDEX idx_logs_fecha
ON logs(fecha_transaccion);

INSERT INTO personas1 (
            documento, tipo_documento, primer_nombre, segundo_nombre, apellidos,
            fecha_nacimiento, genero, correo, celular, foto_url, rol
        ) VALUES (777, 'CC', 'Simon', '', 'Giraldo', '2004-01-01', 'Masculino', 'yop@gmail.com', '3000000000', '777.jpg', 'admin');