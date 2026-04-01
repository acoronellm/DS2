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

@app.route("/eliminar_persona/<documento>", methods=["GET"])
def eliminar_persona(documento):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT foto_url FROM personas1 WHERE documento = %s", (documento,))
        resultado = cur.fetchone()
        if not resultado:
            return "❌ Persona no encontrada", 404

        foto = resultado[0]
        if foto:
            try:
                client.remove_object(BUCKET, foto)
                print(f"Foto eliminada: {foto}")
            except Exception as e:
                print(f"No se pudo eliminar la foto: {e}")

        cur.execute("DELETE FROM personas1 WHERE documento = %s", (documento,))
        conn.commit()
        cur.close()
        conn.close()

        return "✅ Persona eliminada exitosamente", 200

    except Exception as e:
        return f"❌ Error eliminando persona: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)