#op-update/app.py
from flask import Flask, request
from minio import Minio
import psycopg2
import requests
from datetime import datetime

app = Flask(__name__)

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

@app.route("/obtener_persona/<numero_documento>", methods=["GET"])
def obtener_persona(numero_documento):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM personas_registradas WHERE numero_documento = %s", (numero_documento,))
        persona = cur.fetchone()
        if persona:
            persona_dict = {
                "numero_documento": persona[0],
                "tipo_documento_identidad": persona[1],
                "primer_nombre": persona[2],
                "segundo_nombre": persona[3],
                "apellidos": persona[4],
                "fecha_nacimiento": persona[5],
                "genero_persona": persona[6],
                "correo_electronico": persona[7],
                "numero_celular": persona[8],
                "url_foto_perfil": persona[9],
                "rol_usuario": persona[10]
            }

            # 🔥 Manejo seguro de fecha
            fecha_raw = persona_dict["fecha_nacimiento"]

            if fecha_raw:
                if isinstance(fecha_raw, str):
                    fecha_obj = datetime.strptime(fecha_raw, "%a, %d %b %Y %H:%M:%S %Z")
                else:
                    fecha_obj = fecha_raw  # ya es datetime

                persona_dict["fecha_nacimiento"] = fecha_obj.strftime("%Y-%m-%d")
            cur.close()
            conn.close()
            return persona_dict, 200
        else:
            persona_dict = None
            cur.close()
            conn.close()
            return "❌ No se encontró una persona con ese documento", 400
        
    except Exception as e:
        return f"❌ Error conectando con el microservicio: {str(e)}"
    
@app.route("/actualizar_persona", methods=["POST"])
def actualizar_persona():
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

        foto_actual = request.form.get("foto_actual")
        
        foto = request.files.get('foto')

        if foto and foto.filename != "":
            extension = foto.filename.split('.')[-1]
            nombre_archivo = f"{numero_documento}.{extension}"

            try:
                client.remove_object(BUCKET, foto.filename)
                print(f"Foto eliminada: {foto.filename}")
            except Exception as e:
                print(f"No se pudo eliminar la foto: {str(e)}")

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
        else:
            nombre_archivo = foto_actual

        conn = get_connection()
        cur = conn.cursor()

        # Insertar en Postgres
        cur.execute("""
        UPDATE personas_registradas SET
            tipo_documento_identidad=%s,
            primer_nombre=%s,
            segundo_nombre=%s,
            apellidos=%s,
            fecha_nacimiento=%s,
            genero_persona=%s,
            correo_electronico=%s,
            numero_celular=%s,
            url_foto_perfil = COALESCE(%s, url_foto_perfil),
            rol_usuario=%s
        WHERE numero_documento=%s
        """, (
            tipo_documento_identidad, primer_nombre, segundo_nombre, apellidos,
            fecha_nacimiento, genero_persona, correo_electronico, numero_celular, nombre_archivo, rol_usuario, numero_documento
        ))

        conn.commit()
        cur.close()
        conn.close()

        return f"✅ Persona {primer_nombre} actualizada correctamente."

    except Exception as e:
        return f"❌ Error interno: {str(e)}", 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)