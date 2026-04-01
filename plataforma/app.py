from urllib import response

from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
import requests
import os
import docker
import psycopg2

app = Flask(__name__)
app.secret_key = "super_secret_key" 

# URL interna de Docker
OP_CREATE_URL = os.getenv("OP_CREATE_URL", "http://op-create:5001")
OP_UPDATE_URL = os.getenv("OP_UPDATE_URL", "http://op-update:5003")
OP_READ_URL = os.getenv("OP_READ_URL", "http://op-read:5004")
OP_DELETE_URL = os.getenv("OP_DELETE_URL", "http://op-delete:5005")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:5002")
app.consultar_status = True

@app.route("/")
def inicio():
    return render_template_string("""
    <h1>LOGIN</h1>
    
    <form action="/login" method="post">
        Correo electrónico: <input type="email" name="email" required><br>
        Contraseña: <input type="password" name="password" required><br><br>
        <input type="submit" value="Iniciar Sesión">
    """)

@app.route("/login", methods=["POST"])
def login():
    data = request.form
    try:
        res = requests.post(f"{AUTH_SERVICE_URL}/login", json={
            "email": data.get("email"),
            "password": data.get("password")
        })
        if res.status_code == 200 or res.status_code == 201:
            auth_data = res.json()
            session["user"] = auth_data["user"]["email"]
            session["accessToken"] = auth_data["accessToken"]
            session["refreshToken"] = auth_data["refreshToken"]
            obtener_info(session.get("user", "Invitado"))
            return redirect(url_for('menu', email=session["user"], accessToken=session["accessToken"], refreshToken=session["refreshToken"]))
        else:
            return render_template_string("""
            <h1>LOGIN</h1>
            <p style="color:red;"><strong>Credenciales incorrectas</strong></p>
            <form action="/login" method="post">
                Correo electrónico: <input type="email" name="email" required><br>
                Contraseña: <input type="password" name="password" required><br><br>
                <input type="submit" value="Iniciar Sesión">
            """)
    except Exception as e:
        return f"❌ Error conectando con el servicio de autenticación: {str(e)}"
    
# 🔗 PostgreSQL
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
        cur.execute("SELECT * FROM personas1 WHERE correo = %s", (email,))
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
            cur.close()
            conn.close()
            session["documento"] = persona_dict["documento"]
            session["rol"] = persona_dict["rol"]
        else:
            persona_dict = None
            cur.close()
            conn.close()
        
    except Exception as e:
        return f"❌ Error conectando con el microservicio: {str(e)}"

@app.route("/menu")
def menu():
    return render_template_string("""
    <h1>MENÚ PRINCIPAL</h1>
    <h2>Bienvenido, {{ email }}</h2>
    {% if rol == "admin" %}                          
        <p><strong>Access Token:</strong> {{ accessToken }}</p>
        <p><strong>Refresh Token:</strong> {{ refreshToken }}</p>   
        <ul>
            <li><a href="/formulario_crear">Crear persona</a></li>
            <li><a href="/formulario_actualizar">Actualizar persona</a></li>
            <li><a href="/formulario_consultar">Consultar persona</a></li>
            <li><a href="/formulario_eliminar">Eliminar persona</a></li>
            <li>
                <form action="/logout" method="post" style="display:inline;">
                    <button type="submit">Cerrar sesión</button>
                </form>
            </li>
        </ul>
    {% else %}
        <li><a href="/formulario_actualizar">Actualizar persona</a></li>
    {% endif %}
    """, rol=session.get("rol"), email=session.get("user", "Invitado"), accessToken=session.get("accessToken"), refreshToken=session.get("refreshToken"))

@app.route("/logout", methods=["POST"])
def logout():
    try:
        access_token = session.get("accessToken")
        try:
            # Llamar al microservicio de auth para invalidar el token
            if access_token:
                requests.post(
                    f"{AUTH_SERVICE_URL}/logout",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
        except Exception:
            pass

        # Limpiar sesión de Flask
        session.clear()
        return redirect(url_for('inicio'))
    except Exception as e:
        return f"❌ Error conectando con el servicio de autenticación: {str(e)}"

# ---------------- Pausar contenedor ----------------
@app.route("/pause", methods=["POST"])
def pause_route():
    try:
        nombre = request.form["container_name"]
        pause_container(nombre)
        return redirect(url_for('formulario_consultar'))
    except Exception as e:
        return f"error {str(e)}", 500
    
def pause_container(container_name):
    client = docker.from_env()
    try:
        container = client.containers.get(container_name)
        container.pause()
        app.consultar_status = False
        return f"⏸️ Contenedor '{container_name}' pausado exitosamente."
    except docker.errors.NotFound:
        return f"ERROR\nEl contenedor '{container_name}' no existe."
    except Exception as e:
        return f"Error al pausar el contenedor: {str(e)}"

# ---------------- Reanudar contenedor ----------------
@app.route("/resume", methods=["POST"])
def resume_route():
    try:
        nombre = request.form["container_name"]
        resume_container(nombre)
        return redirect(url_for('formulario_consultar'))
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
            return f"▶️ Contenedor '{name}' reanudado exitosamente."

        if container.status in ["exited", "dead", "created", "stopped"]:
            container.start()
            app.consultar_status = True
            return f"▶️ Contenedor '{name}' iniciado exitosamente."

        if container.status == "running":
            app.consultar_status = True
            return f"▶️ Contenedor '{name}' ya estaba en ejecución."

        return f"❌ Estado no manejado: {container.status}"
    
    except docker.errors.NotFound:
        return f"❌ Error: Contenedor '{name}' no existe"
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route("/formulario_eliminar")
def formulario_eliminar():
    return render_template_string("""
    <h1>ELIMINAR PERSONA</h1>
    <form action="/eliminar_persona" method="get">
        Nro. Documento: <input type="text" name="documento" maxlength="10" pattern="[0-9]+" required><br><br>
        <input type="submit" value="Eliminar Persona">
    </form>
    <br>
    <a href="/menu">⬅ Volver al menú</a>
    """)

@app.route("/eliminar_persona", methods=["GET"])
def eliminar_persona():
    try:
        documento = request.args.get("documento")
        response = requests.get(f"{OP_DELETE_URL}/eliminar_persona/{documento}")
        return render_template_string("""
        <h1>RESULTADO DE LA ELIMINACIÓN</h1>
        <p>{{ mensaje }}</p>
        <br>
        <a href="/formulario_eliminar">⬅ Eliminar otra persona</a><br>
        <a href="/menu">⬅ Volver al menú</a>
        """, mensaje=response.text)
    except Exception as e:
        print(f"Error eliminando persona: {str(e)}")
        return f"❌ Error eliminando persona: {str(e)}"

@app.route("/formulario_consultar")
def formulario_consultar():
    return render_template_string("""
    <h1>CONSULTAR DATOS PERSONALES</h1>
    {% if status %}
        <form action="/consultar_persona" method="get">
            Nro. Documento: <input type="text" name="documento" maxlength="10" pattern="[0-9]+" required><br><br>
            <input type="submit" value="Consultar Persona">
        </form>
    {% else %}
        <p style="color:red;"><strong>El microservicio de consulta no está disponible</strong></p>
    {% endif %}
    <form action="/pause" method="post" style="display:inline;">
        <input type="hidden" name="container_name" value="op-read">
        <input type="submit" value="⏸️ Pausar Consulta">
    </form>
    <form action="/resume" method="post" style="display:inline;">
        <input type="hidden" name="container_name" value="op-read">
        <input type="submit" value="▶️ Reanudar Consulta">
    </form>
    <br>
    <a href="/menu">⬅ Volver al menú</a>
    """, status=app.consultar_status)

@app.route("/consultar_persona", methods=["GET"])
def consultar_persona():
    documento = request.args.get("documento")
    persona = obtener_persona1(documento) if documento else None
    return render_template_string("""
    <h1>INFORMACION OBTENIDA DEL USUARIO</h1>

    {% if persona %}
        <p><strong>Documento:</strong> {{ persona.documento }}</p>
        <p><strong>Tipo:</strong> {{ persona.tipo_documento }}</p>
        <p><strong>Nombre:</strong> {{ persona.primer_nombre }}</p>
        <p><strong>Segundo Nombre:</strong> {{ persona.segundo_nombre }}</p>
        <p><strong>Apellidos:</strong> {{ persona.apellidos }}</p>
        <p><strong>Fecha Nacimiento:</strong> {{ persona.fecha_nacimiento }}</p>
        <p><strong>Género:</strong> {{ persona.genero }}</p>
        <p><strong>Email:</strong> {{ persona.correo }}</p>
        <p><strong>Celular:</strong> {{ persona.celular }}</p>
        <p><strong>Foto URL:</strong> {{ persona.foto_url }}</p>
        {% if persona and persona.foto_url %}
        <p><strong>Foto:</strong></p>
        <img src="http://localhost:9000/fotos-personas/{{ persona.foto_url }}" width="200">
        {% endif %}
        <p><strong>Rol:</strong> {{ persona.rol }}</p>
    {% else %}
        <p style="color:red;"><strong>No se encontró la persona</strong></p>
    {% endif %}

    <br>
    <a href="/formulario_consultar">⬅ Realizar otra consulta</a>
    <br>
    <a href="/menu">⬅ Volver al menú</a>

    <pre>{{ persona }}</pre>
    """, persona=persona)

def obtener_persona1(documento):
    try:
        response = requests.get(f"{OP_READ_URL}/obtener_persona/{documento}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error obteniendo persona: {str(e)}")
        return None

def obtener_persona(documento):
    try:
        response = requests.get(f"{OP_UPDATE_URL}/obtener_persona/{documento}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error obteniendo persona: {str(e)}")
        return None

@app.route("/formulario_actualizar")
def formulario_actualizar():
    documento = session.get("documento")
    #documento = "4"  # Para pruebas, se puede cambiar por un input en el futuro
    persona = obtener_persona(documento) if documento else None
    return render_template_string("""
    <h1>MODIFICAR DATOS PERSONALES</h1>
                                  
    {% if persona %}
                                  
        <form action="/actualizar_persona" method="post" enctype="multipart/form-data">
                                    
            Nro. Documento:
            <input type="text" name="documento" value="{{ persona.documento if persona else '' }}" readonly><br>

            Tipo de documento:
            <select name="tipo_documento" required>
                <option value="">Seleccione</option>
                <option value="TI"
                    {% if persona and persona.tipo_documento == "TI" %}selected{% endif %}>
                    Tarjeta de identidad
                </option>
                <option value="CC"
                    {% if persona and persona.tipo_documento == "CC" %}selected{% endif %}>
                    Cédula
                </option>
            </select><br>
                                    
            Primer Nombre:
            <input type="text" name="primer_nombre" value="{{ persona.primer_nombre if persona else '' }}" maxlength="30" pattern="[A-Za-z ]+" required><br>

            Segundo Nombre:
            <input type="text" name="segundo_nombre" value="{{ persona.segundo_nombre if persona else '' }}" maxlength="30" pattern="[A-Za-z ]+"><br>

            Apellidos:
            <input type="text" name="apellidos" value="{{ persona.apellidos if persona else '' }}" maxlength="60" pattern="[A-Za-z ]+" required><br>

            Fecha Nacimiento: <input type="date" name="fecha_nacimiento" value="{{ persona.fecha_nacimiento if persona else '' }}" required><br>

            Genero:
            <select name="genero" required>
                <option value="">Seleccione</option>
                <option value="Masculino"
                    {% if persona and persona.genero == "Masculino" %}selected{% endif %}>
                    Masculino
                </option>
                <option value="Femenino"
                    {% if persona and persona.genero == "Femenino" %}selected{% endif %}>
                    Femenino
                </option>
                <option value="No binario"
                    {% if persona and persona.genero == "No binario" %}selected{% endif %}>
                    No binario
                </option>
                <option value="Prefiero no reportar"
                    {% if persona and persona.genero == "Prefiero no reportar" %}selected{% endif %}>
                    Prefiero no reportar
                </option>
            </select><br>

            Correo electrónico:
            <input type="email" name="correo" value="{{ persona.correo if persona else '' }}" required><br>

            Celular:
            <input type="text" name="celular" value="{{ persona.celular if persona else '' }}" maxlength="10" pattern="[0-9]{10}" required><br><br>

            <input type="hidden" name="foto_actual" value="{{ persona.foto_url }}">

            {% if persona and persona.foto_url %}
            <p><strong>Foto actual:</strong></p>
            <img src="http://localhost:9000/fotos-personas/{{ persona.foto_url }}" width="200"><br>
            {% endif %}                                  

            Foto: <input type="file" name="foto" ><br><br>
                                  
            Rol:
            <select disabled>
                <option value="">Seleccione</option>
                <option value="admin"
                    {% if persona and persona.rol == "admin" %}selected{% endif %}>
                    admin
                </option>
                <option value="user"
                    {% if persona and persona.rol == "user" %}selected{% endif %}>
                    user
                </option>
            </select>

            <input type="hidden" name="rol" value="{{ persona.rol }}"><br>

            <input type="submit" value="Actualizar Persona">
        </form>
                                  
    {% else %}
        <p style="color:red;"><strong>No se encontró la persona</strong></p>
    {% endif %}
                                  
    <br>
    <a href="/menu">⬅ Volver al menú</a>
    <pre>{{ persona }}</pre>
    """, persona=persona)

@app.route("/actualizar_persona", methods=["POST"])
def actualizar_persona():
    try:

        files = {}
        if 'foto' in request.files and request.files['foto'].filename != "":
            files["foto"] = (
                request.files['foto'].filename,
                request.files['foto'],
                request.files['foto'].content_type
            )

        response = requests.post(
            f"{OP_UPDATE_URL}/actualizar_persona",
            data=request.form,
            files=files
        )

        rol_nuevo = request.form.get("rol")
        session["rol"] = rol_nuevo
        session["documento"] = request.form.get("documento")
        session["user"] = request.form.get("correo")

        return render_template_string("""
        <h1>RESULTADO DE ACTUALIZACION</h1>
        <p>{{ mensaje }}</p>

        <br>
        <a href="/formulario_actualizar">⬅ Realizar otra actualizacion</a><br>
        <a href="/menu">⬅ Volver al menú</a>
        """, mensaje=response.text)
    except Exception as e:
        return f"❌ Error conectando con el microservicio: {str(e)}"

@app.route("/formulario_crear")
def formulario_crear():
    return render_template_string("""
    <h1>CREACION DE PERSONA</h1>
    <form action="/crear_persona" method="post" enctype="multipart/form-data">
        
        Nro. Documento:
        <input type="text" name="documento" maxlength="10" pattern="[0-9]+" required><br>
        
        Tipo de documento:
        <select name="tipo_documento" required>
            <option value="">Seleccione</option>
            <option value="TI">Tarjeta de identidad</option>
            <option value="CC">Cedula</option>
        </select><br>

        Primer Nombre:
        <input type="text" name="primer_nombre" maxlength="30" pattern="[A-Za-z ]+" required><br>

        Segundo Nombre:
        <input type="text" name="segundo_nombre" maxlength="30" pattern="[A-Za-z ]+"><br>

        Apellidos:
        <input type="text" name="apellidos" maxlength="60" pattern="[A-Za-z ]+" required><br>

        Fecha de Nacimiento:
        <input type="date" name="fecha_nacimiento" required><br>

        Género:
        <select name="genero" required>
            <option value="">Seleccione</option>
            <option>Masculino</option>
            <option>Femenino</option>
            <option>No binario</option>
            <option>Prefiero no reportar</option>
        </select><br>

        Correo electrónico:
        <input type="email" name="correo" required><br>

        Celular:
        <input type="text" name="celular" maxlength="10" pattern="[0-9]{10}" required><br><br>
                                  
        Foto: <input type="file" name="foto" required><br><br>
                                  
        Rol:
        <select name="rol" required>
            <option value="">Seleccione</option>
            <option>admin</option>
            <option>user</option>
        </select><br>

        Contraseña:
        <input type="password" name="password" required><br><br>

        <input type="submit" value="Guardar Persona">
    </form>
    <br>
    <a href="/menu">⬅ Volver al menú</a>
    """)

@app.route("/crear_persona", methods=["POST"])
def crear_persona():
    try:
        
        response = requests.post(
            f"{OP_CREATE_URL}/crear_persona",
            data=request.form,
            files={
                "foto": (
                    request.files['foto'].filename,
                    request.files['foto'],
                    request.files['foto'].content_type
                )
            }
        )

        return render_template_string("""
        <h1>RESULTADO DE CREACION</h1>
        <p>{{ mensaje }}</p>

        <br>
        <a href="/formulario_crear">⬅ Realizar otra creación</a><br>
        <a href="/menu">⬅ Volver al menú</a>
        """, mensaje=response.text)
    except Exception as e:
        return f"❌ Error conectando con el microservicio: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)