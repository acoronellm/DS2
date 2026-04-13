#op-create/app.py:
from flask import Flask, request
from minio import Minio
import psycopg2
import os
import requests

app = Flask(__name__)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:5002")
OP_DELETE_URL = os.getenv("OP_DELETE_URL", "http://op-delete:5005")

# 🔗 MinIO
client = Minio(
    "minio:9000",
    access_key="admin",
    secret_key="admin123",
    secure=False
)

# 🔗 PostgreSQL
def get_connection():
    return psycopg2.connect(
        host="postgres",
        port="5432",
        database="personas_db",
        user="admin",
        password="admin123"
    )

BUCKET = "fotos-personas"

@app.route("/crear_persona", methods=["POST"])
def crear_persona():
    try:
        # Extraer datos del formulario
        tipo_documento_identidad = request.form['tipo_documento_identidad']
        numero_documento = request.form['numero_documento']
        primer_nombre = request.form['primer_nombre']
        segundo_nombre = request.form['segundo_nombre']
        apellidos = request.form['apellidos']
        fecha_nacimiento = request.form['fecha_nacimiento']
        genero_persona = request.form['genero_persona']
        correo_electronico = request.form['correo_electronico']
        numero_celular = request.form['numero_celular']
        rol_usuario = request.form['rol_usuario']
        password = request.form['password']
        
        # Manejo de la foto
        if 'foto' not in request.files:
            return "❌ No se subió ninguna foto", 400
            
        foto = request.files['foto']
        extension = foto.filename.split('.')[-1]
        nombre_archivo = f"{numero_documento}.{extension}"

        conn = get_connection()
        cur = conn.cursor()

        # Validar si ya existe
        cur.execute("SELECT * FROM personas_registradas WHERE numero_documento = %s", (numero_documento,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return "❌ Ya existe una persona con ese documento", 400

        # Asegurar bucket en MinIO
        if not client.bucket_exists(BUCKET):
            client.make_bucket(BUCKET)

        # Subir a MinIO
        client.put_object(
            BUCKET,
            nombre_archivo,
            foto,
            length=-1,
            part_size=10*1024*1024
        )
        subido_a_minio = True

        # Insertar en Postgres
        cur.execute("""
        INSERT INTO personas_registradas (
            numero_documento, tipo_documento_identidad, primer_nombre, segundo_nombre, apellidos,
            fecha_nacimiento, genero_persona, correo_electronico, numero_celular, url_foto_perfil, rol_usuario
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            numero_documento, tipo_documento_identidad, primer_nombre, segundo_nombre, apellidos,
            fecha_nacimiento, genero_persona, correo_electronico, numero_celular, nombre_archivo, rol_usuario
        ))

        conn.commit()
        cur.close()
        conn.close()
        creado_en_postgres = True

        res = requests.post(
            f"{AUTH_SERVICE_URL}/signup",
            json={
                "email": correo_electronico,
                "password": password,
                "name": primer_nombre + " " + segundo_nombre + " " + apellidos
            }
        )
        if res.status_code not in [200, 201]:
            return f"❌ Error creando usuario (ROBLE): {res.text}", 400

        return f"✅ Persona {primer_nombre} creada correctamente."

    except Exception as e:
        if creado_en_postgres:
            requests.get(f"{OP_DELETE_URL}/eliminar_persona/{numero_documento}")

        elif subido_a_minio:
            try:
                client.remove_object(BUCKET, nombre_archivo)
            except:
                pass
        return f"❌ Error interno: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)