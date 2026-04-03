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
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)