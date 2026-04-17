#op-read/app.py
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

from datetime import datetime

@app.route("/obtener_logs2/<fecha_transaccion>", methods=["GET"])
def obtener_logs2(fecha_transaccion):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT tipo_operacion, numero_documento, fecha_transaccion, detalle
            FROM logs
            WHERE DATE(fecha_transaccion) = %s
        """, (fecha_transaccion,))

        logs = cur.fetchall()

        if logs:
            log_list = []

            for log in logs:
                fecha_raw = log[2]

                if fecha_raw:
                    fecha_final = fecha_raw.strftime("%Y-%m-%d")
                else:
                    fecha_final = None

                log_list.append({
                    "tipo_operacion": log[0],
                    "numero_documento": log[1],
                    "fecha_transaccion": fecha_final,
                    "detalle": log[3]
                })

            cur.close()
            conn.close()
            return {"logs": log_list}, 200
        else:
            return {"mensaje": "No se encontraron logs"}, 404

    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/obtener_logs/<numero_documento>/<tipo_operacion>", methods=["GET"])
def obtener_logs(numero_documento, tipo_operacion):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT tipo_operacion, numero_documento, fecha_transaccion, detalle
            FROM logs
            WHERE numero_documento = %s AND tipo_operacion = %s
        """, (numero_documento, tipo_operacion))

        logs = cur.fetchall()

        if logs:
            log_list = [
                {
                    "tipo_operacion": log[0],
                    "numero_documento": log[1],
                    "fecha_transaccion": str(log[2]),  # convertir DATE a string
                    "detalle": log[3]
                }
                for log in logs
            ]
            cur.close()
            conn.close()
            return {"logs": log_list}, 200
        else:
            return {"mensaje": "No se encontraron logs"}, 404

    except Exception as e:
        return {"error": str(e)}, 500

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
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)