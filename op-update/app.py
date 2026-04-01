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

@app.route("/obtener_persona/<documento>", methods=["GET"])
def obtener_persona(documento):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM personas1 WHERE documento = %s", (documento,))
        persona = cur.fetchone()
        if persona:
            persona_dict = {
                "documento": persona[0],
                "tipo_documento": persona[1],
                "primer_nombre": persona[2],
                "segundo_nombre": persona[3],
                "apellidos": persona[4],
                "fecha_nacimiento": persona[5],
                "genero": persona[6],
                "correo": persona[7],
                "celular": persona[8],
                "foto_url": persona[9],
                "rol": persona[10]
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
        tipo_documento = request.form['tipo_documento']
        documento = request.form['documento']
        primer_nombre = request.form['primer_nombre']
        segundo_nombre = request.form['segundo_nombre']
        apellidos = request.form['apellidos']
        fecha_nacimiento = request.form['fecha_nacimiento']
        genero = request.form['genero']
        correo = request.form['correo']
        celular = request.form['celular']
        rol = request.form['rol']

        foto_actual = request.form.get("foto_actual")
        
        foto = request.files.get('foto')

        if foto and foto.filename != "":
            extension = foto.filename.split('.')[-1]
            nombre_archivo = f"{documento}.{extension}"

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
        UPDATE personas1 SET
            tipo_documento=%s,
            primer_nombre=%s,
            segundo_nombre=%s,
            apellidos=%s,
            fecha_nacimiento=%s,
            genero=%s,
            correo=%s,
            celular=%s,
            foto_url = COALESCE(%s, foto_url),
            rol=%s
        WHERE documento=%s
        """, (
            tipo_documento, primer_nombre, segundo_nombre, apellidos,
            fecha_nacimiento, genero, correo, celular, nombre_archivo, rol, documento
        ))

        conn.commit()
        cur.close()
        conn.close()

        return f"✅ Persona {primer_nombre} actualizada correctamente."

    except Exception as e:
        return f"❌ Error interno: {str(e)}", 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)