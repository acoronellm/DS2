from flask import Flask, request, render_template, redirect, url_for, session
import requests
import os
import docker
import psycopg2

app = Flask(
    __name__,
    template_folder="ventanas",
    static_folder="static"
)

app.secret_key = "super_secret_key"

OP_CREATE_URL = os.getenv("OP_CREATE_URL", "http://op-create:5001")
OP_UPDATE_URL = os.getenv("OP_UPDATE_URL", "http://op-update:5003")
OP_READ_URL = os.getenv("OP_READ_URL", "http://op-read:5004")
OP_DELETE_URL = os.getenv("OP_DELETE_URL", "http://op-delete:5005")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:5002")

app.consultar_status = True


@app.route("/")
def inicio():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    data = request.form

    try:
        res = requests.post(f"{AUTH_SERVICE_URL}/login", json={
            "email": data.get("email"),
            "password": data.get("password")
        })

        if res.status_code in [200, 201]:
            auth_data = res.json()

            session["user"] = auth_data["user"]["email"]
            session["accessToken"] = auth_data["accessToken"]
            session["refreshToken"] = auth_data["refreshToken"]

            obtener_info(session.get("user", "Invitado"))

            return redirect(url_for("menu"))

        return render_template("login.html", error="Credenciales incorrectas")

    except Exception as e:
        return f"❌ Error conectando con el servicio de autenticación: {str(e)}"


def get_connection():
    return psycopg2.connect(
        host="postgres",
        port="5432",
        database="personas_db",
        user="admin",
        password="admin123"
    )


def obtener_info(email):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM personas_registradas WHERE correo_electronico = %s",
            (email,)
        )

        persona = cur.fetchone()

        cur.close()
        conn.close()

        if persona:
            session["numero_documento"] = persona[0]
            session["rol_usuario"] = persona[10]

    except Exception as e:
        print(f"Error obteniendo información del usuario: {str(e)}")


@app.route("/menu")
def menu():
    return render_template(
        "menu.html",
        rol_usuario=session.get("rol_usuario"),
        email=session.get("user", "Invitado"),
        vista="inicio"
    )


@app.route("/logout", methods=["POST"])
def logout():
    try:
        access_token = session.get("accessToken")

        if access_token:
            try:
                requests.post(
                    f"{AUTH_SERVICE_URL}/logout",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
            except Exception:
                pass

        session.clear()
        return redirect(url_for("inicio"))

    except Exception as e:
        return f"❌ Error cerrando sesión: {str(e)}"


def registrar_log_contenedor(detalle):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO logs (
                tipo_operacion,
                numero_documento,
                fecha_transaccion,
                detalle
            ) VALUES (%s, %s, NOW(), %s)
        """, ("READ", session.get("numero_documento", ""), detalle))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error registrando log: {str(e)}")


@app.route("/pause", methods=["POST"])
def pause_route():
    try:
        nombre = request.form["container_name"]
        pause_container(nombre)
        return redirect(url_for("formulario_consultar"))

    except Exception as e:
        return f"error {str(e)}", 500


def pause_container(container_name):
    client = docker.from_env()

    try:
        container = client.containers.get(container_name)
        container.pause()

        app.consultar_status = False
        registrar_log_contenedor("El contenedor de consulta fue pausado")

        return f"⏸️ Contenedor '{container_name}' pausado exitosamente."

    except docker.errors.NotFound:
        return f"ERROR\nEl contenedor '{container_name}' no existe."

    except Exception as e:
        return f"Error al pausar el contenedor: {str(e)}"


@app.route("/resume", methods=["POST"])
def resume_route():
    try:
        nombre = request.form["container_name"]
        resume_container(nombre)
        return redirect(url_for("formulario_consultar"))

    except Exception as e:
        return f"error {str(e)}", 500


def resume_container(name):
    client = docker.from_env()

    try:
        container = client.containers.get(name)
        container.reload()

        if container.status == "paused":
            container.unpause()
            app.consultar_status = True
            registrar_log_contenedor("El contenedor de consulta fue reanudado")
            return f"▶️ Contenedor '{name}' reanudado exitosamente."

        if container.status in ["exited", "dead", "created", "stopped"]:
            container.start()
            app.consultar_status = True
            registrar_log_contenedor("El contenedor de consulta fue iniciado")
            return f"▶️ Contenedor '{name}' iniciado exitosamente."

        if container.status == "running":
            app.consultar_status = True
            return f"▶️ Contenedor '{name}' ya estaba en ejecución."

        return f"❌ Estado no manejado: {container.status}"

    except docker.errors.NotFound:
        return f"❌ Error: Contenedor '{name}' no existe."

    except Exception as e:
        return f"❌ Error: {str(e)}"


@app.route("/llamado_logs")
def llamado_logs():
    return render_template(
        "logs.html",
        rol_usuario=session.get("rol_usuario")
    )


@app.route("/busqueda_logs", methods=["GET"])
def busqueda_logs():
    numero_documento = request.args.get("numero_documento")
    tipo_operacion = request.args.get("tipo_operacion")

    try:
        response = requests.get(
            f"{OP_READ_URL}/obtener_logs/{numero_documento}/{tipo_operacion}"
        )

        logs = response.json().get("logs", []) if response.status_code == 200 else []

        return render_template(
            "resultado_logs.html",
            logs=logs,
            rol_usuario=session.get("rol_usuario")
        )

    except Exception as e:
        return f"❌ Error conectando con el microservicio: {str(e)}"


@app.route("/busqueda_logs2", methods=["GET"])
def busqueda_logs2():
    fecha_transaccion = request.args.get("fecha_transaccion")

    try:
        response = requests.get(
            f"{OP_READ_URL}/obtener_logs2/{fecha_transaccion}"
        )

        logs = response.json().get("logs", []) if response.status_code == 200 else []

        return render_template(
            "resultado_logs.html",
            logs=logs,
            rol_usuario=session.get("rol_usuario")
        )

    except Exception as e:
        return f"❌ Error conectando con el microservicio: {str(e)}"


@app.route("/formulario_crear")
def formulario_crear():
    return render_template(
        "formulario_crear.html",
        email=session.get("user", "Invitado"),
        rol_usuario=session.get("rol_usuario")
    )


@app.route("/crear_persona", methods=["POST"])
def crear_persona():
    try:
        documento = session.get("numero_documento", "")

        files = {}

        if "foto" in request.files and request.files["foto"].filename != "":
            files["foto"] = (
                request.files["foto"].filename,
                request.files["foto"],
                request.files["foto"].content_type
            )

        response = requests.post(
            f"{OP_CREATE_URL}/crear_persona/{documento}",
            data=request.form,
            files=files
        )

        return render_template(
            "resultado_crear.html",
            mensaje=response.text,
            email=session.get("user", "Invitado"),
            rol_usuario=session.get("rol_usuario")
        )

    except Exception as e:
        return render_template(
            "resultado_crear.html",
            mensaje=f"❌ Error conectando con el microservicio: {str(e)}",
            email=session.get("user", "Invitado"),
            rol_usuario=session.get("rol_usuario")
        )


@app.route("/formulario_actualizar")
def formulario_actualizar():
    rol = session.get("rol_usuario", "").lower()

    if rol == "user":
        return redirect(url_for("buscar_actualizar"))

    return render_template(
        "buscar_actualizar.html",
        email=session.get("user", "Invitado"),
        rol_usuario=rol,
        ocultar_menu=(rol == "user")  # siempre False aquí, porque el user ya fue redirigido
    )

@app.route("/buscar_actualizar", methods=["GET"])
def buscar_actualizar():

    rol = session.get("rol_usuario", "").lower()

    if rol == "user":
        numero_documento = session.get("numero_documento")
    else:
        numero_documento = request.args.get("numero_documento")

    persona = obtener_persona(numero_documento) if numero_documento else None

    return render_template(
        "formulario_actualizar.html",
        persona=persona,
        email=session.get("user", "Invitado"),
        rol_usuario=rol,
        ocultar_menu=(rol == "user")
    )


@app.route("/actualizar_persona", methods=["POST"])
def actualizar_persona():

    try:

        files = {}

        if "foto" in request.files and request.files["foto"].filename != "":

            files["foto"] = (
                request.files["foto"].filename,
                request.files["foto"],
                request.files["foto"].content_type
            )

        documento_auditor = session.get("numero_documento", "")

        response = requests.post(
            f"{OP_UPDATE_URL}/actualizar_persona/{documento_auditor}",
            data=request.form,
            files=files
        )

        return render_template(
            "resultado_actualizar.html",
            mensaje=response.text,
            email=session.get("user", "Invitado"),
            rol_usuario=session.get("rol_usuario", "").lower(),
            ocultar_menu=(session.get("rol_usuario", "").lower() == "user")
        )

    except Exception as e:

        return render_template(
            "resultado_actualizar.html",
            mensaje=f"❌ Error interno: {str(e)}",
            email=session.get("user", "Invitado"),
            rol_usuario=session.get("rol_usuario", "").lower(),
            ocultar_menu=(session.get("rol_usuario", "").lower() == "user")
        )

@app.route("/formulario_consultar")
def formulario_consultar():
    return render_template(
        "formulario_consultar.html",
        status=app.consultar_status,
        email=session.get("user", "Invitado"),
        rol_usuario=session.get("rol_usuario")
    )


@app.route("/consultar_persona", methods=["GET"])
def consultar_persona():
    numero_documento = request.args.get("numero_documento")
    persona = obtener_persona1(numero_documento) if numero_documento else None

    return render_template(
        "resultado_consulta.html",
        persona=persona,
        email=session.get("user", "Invitado"),
        rol_usuario=session.get("rol_usuario")
    )


def obtener_persona1(numero_documento):
    try:
        documento = session.get("numero_documento", "")

        response = requests.get(
            f"{OP_READ_URL}/obtener_persona1/{numero_documento}/{documento}"
        )

        if response.status_code == 200:
            return response.json()

        return None

    except Exception as e:
        print(f"Error obteniendo persona: {str(e)}")
        return None


def obtener_persona(numero_documento):
    try:
        response = requests.get(
            f"{OP_UPDATE_URL}/obtener_persona/{numero_documento}"
        )

        if response.status_code == 200:
            return response.json()

        return None

    except Exception as e:
        print(f"Error obteniendo persona: {str(e)}")
        return None


@app.route("/formulario_eliminar")
def formulario_eliminar():
    return render_template(
        "formulario_eliminar.html",
        email=session.get("user", "Invitado"),
        rol_usuario=session.get("rol_usuario")
    )


@app.route("/eliminar_persona", methods=["GET"])
def eliminar_persona():
    try:
        numero_documento = request.args.get("numero_documento")
        documento = session.get("numero_documento", "")

        response = requests.get(
            f"{OP_DELETE_URL}/eliminar_persona/{numero_documento}/{documento}"
        )

        return render_template(
            "resultado_eliminar.html",
            mensaje=response.text,
            email=session.get("user", "Invitado"),
            rol_usuario=session.get("rol_usuario")
        )

    except Exception as e:
        print(f"Error eliminando persona: {str(e)}")

        return render_template(
            "resultado_eliminar.html",
            mensaje=f"❌ Error eliminando persona: {str(e)}",
            email=session.get("user", "Invitado"),
            rol_usuario=session.get("rol_usuario")
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)