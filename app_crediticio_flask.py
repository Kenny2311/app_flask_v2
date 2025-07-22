from flask import Flask, render_template, request, redirect, url_for, session, Response, flash # Añadido 'flash'
import psycopg2
import hashlib
import joblib
import numpy as np
import pandas as pd
import datetime
import plotly.express as px
import plotly
import json
from math import ceil
from collections import namedtuple

from functools import wraps # Asegurarse de que solo haya una importación

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_sesiones' # Reemplaza con una clave secreta fuerte

# ========================
# Decorador para verificar sesión
# ========================
def login_requerido(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        # Verificar 'usuario', 'usuario_id' Y 'rol'
        if 'usuario' not in session or 'usuario_id' not in session or 'rol' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorada

# ========================
# Decorador para verificar roles
# ========================
def role_requerido(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get('rol', '').lower() 
            lower_allowed_roles = [role.lower() for role in allowed_roles]

            if user_role not in lower_allowed_roles:
                return "Acceso denegado: No tienes permiso para ver esta página.", 403 
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ========================
# Cargar modelo
# ========================
try:
    model = joblib.load('modelo_crediticio.pkl')
except FileNotFoundError:
    print("Error: 'modelo_crediticio.pkl' no encontrado. Asegúrate de que el archivo del modelo esté en la ruta correcta.")
    model = None 

# ========================
# Conexión a base de datos
# ========================
def conectar():
    return psycopg2.connect(
        host="dpg-d1vle395pdvs73e8gjeg-a",
        database="creditos_fintech",
        user="creditos_fintech_user",
        password="sPoe16PxHqXrTwsZQpzbqmw9DSggAYoW" # Asegúrate de que esta sea tu contraseña real
    )

def encriptar(contrasena):
    return hashlib.sha256(contrasena.encode()).hexdigest()

# ========================
# Rutas
# ========================
# Ruta principal (menú)
@app.route('/')
def index():
    if 'usuario' in session:
        return render_template('menu.html', usuario=session['usuario'], rol=session.get('rol', ''))
    else:
        return render_template('inicio.html')  # Mostrará inicio sin redirigir al login

@app.route('/inicio')
def inicio():
    return render_template('inicio.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = encriptar(request.form['contrasena'])

        conn = conectar()
        cur = conn.cursor()

        cur.execute("SELECT id, rol FROM usuarios WHERE nombre_usuario=%s AND contrasena=%s", (usuario, contrasena))
        user = cur.fetchone()
        conn.close()

        if user:
            session['usuario'] = usuario
            session['usuario_id'] = user[0]
            session['rol'] = user[1]
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos')
            return render_template('login.html')
    else:
        return render_template('login.html')

# Registro
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombres = request.form['nombres']
        apellidos = request.form['apellidos']
        dni = request.form['dni']
        correo = request.form['correo']
        celular = request.form['celular']
        genero = request.form['genero']
        usuario = request.form['usuario']
        contrasena = request.form['contrasena'] # No encriptar antes de comparar
        confirmar_contrasena = request.form['confirmar_contrasena'] # No encriptar antes de comparar
        rol = request.form.get('rol', 'usuario_basico')

        # Validar contraseña
        if contrasena != confirmar_contrasena:
            flash("Las contraseñas no coinciden. Por favor, vuelve a intentarlo.")
            return render_template('registro.html') # Retornar la plantilla para mostrar el mensaje

        contrasena_encriptada = encriptar(contrasena) # Encriptar solo si coinciden

        conn = conectar()
        cur = conn.cursor()

        # Verificar si el usuario ya existe
        cur.execute("SELECT * FROM usuarios WHERE nombre_usuario=%s", (usuario,))
        if cur.fetchone():
            conn.close()
            flash("El usuario ya existe. Por favor, elige otro nombre de usuario.")
            return render_template('registro.html') # Retornar la plantilla para mostrar el mensaje

        # Insertar nuevo usuario
        cur.execute("""
            INSERT INTO usuarios (
                nombre_usuario, contrasena, rol,
                nombres, apellidos, dni, correo, celular, genero
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (usuario, contrasena_encriptada, rol, nombres, apellidos, dni, correo, celular, genero))

        conn.commit()
        conn.close()
        flash("Registro exitoso. ¡Ahora puedes iniciar sesión!")
        return redirect(url_for('login'))

    return render_template('registro.html')

#Perfil
@app.route('/perfil')
@login_requerido 
def ver_perfil():
    usuario_nombre = session.get('usuario')  # Este es el nombre de usuario guardado al iniciar sesión

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT nombre_usuario, rol, nombres, apellidos, dni, correo, celular, genero
        FROM usuarios WHERE nombre_usuario = %s
    """, (usuario_nombre,))
    
    datos = cur.fetchone()
    conn.close()

    if datos:
        campos = ['nombre_usuario', 'rol', 'nombres', 'apellidos', 'dni', 'correo', 'celular', 'genero']
        usuario = dict(zip(campos, datos))  # Convertimos la tupla en diccionario
        return render_template('perfil.html', usuario=usuario)
    else:
        flash("No se encontró el perfil del usuario.")
        return redirect(url_for('login'))

#Editar perfil
@app.route('/editar_perfil', methods=['GET', 'POST'])
@login_requerido
def editar_perfil():
    usuario_nombre = session.get('usuario')

    conn = conectar()
    cur = conn.cursor()

    if request.method == 'POST':
        # Recibe los datos del formulario
        nombres = request.form['nombres']
        apellidos = request.form['apellidos']
        correo = request.form['correo']
        celular = request.form['celular']

        nueva_contraseña = request.form.get('nueva_contraseña')
        confirmar_contraseña = request.form.get('confirmar_contraseña')

        # Actualiza los datos en la base de datos
        if nueva_contraseña:
            if nueva_contraseña != confirmar_contraseña:
                flash("Las contraseñas no coinciden.", "danger")
                return redirect(url_for('editar_perfil'))
            else:
                contraseña_hash = generate_password_hash(nueva_contraseña)
                cur.execute("""
                    UPDATE usuarios SET nombres=%s, apellidos=%s, correo=%s, celular=%s, contraseña=%s
                    WHERE nombre_usuario=%s
                """, (nombres, apellidos, correo, celular, contraseña_hash, usuario_nombre))
        else:
            cur.execute("""
                UPDATE usuarios SET nombres=%s, apellidos=%s, correo=%s, celular=%s
                WHERE nombre_usuario=%s
            """, (nombres, apellidos, correo, celular, usuario_nombre))

        conn.commit()
        conn.close()
        flash("Perfil actualizado correctamente.")
        return redirect(url_for('ver_perfil'))

    # GET: obtener datos actuales
    cur.execute("""
        SELECT nombres, apellidos, correo, celular
        FROM usuarios WHERE nombre_usuario = %s
    """, (usuario_nombre,))
    datos = cur.fetchone()
    conn.close()

    if datos:
        campos = ['nombres', 'apellidos', 'correo', 'celular']
        usuario = dict(zip(campos, datos))
        return render_template('editar_perfil.html', usuario=usuario)
    else:
        flash("No se encontró el usuario.")
        return redirect(url_for('ver_perfil'))


# Predicción
@app.route('/prediccion', methods=['GET', 'POST'])
@login_requerido
@role_requerido(['administrador', 'analista', 'usuario_basico']) 
def prediccion():
    resultado = None
    if request.method == 'POST':
        if model is None:
            flash("Error: Modelo de predicción no cargado. Contacta al administrador.")
            return render_template('prediccion.html', usuario=session['usuario'], resultado=resultado)

        data = request.form
        try:
            genero_val = data.get('genero')
            casado_val = data.get('casado')
            educacion_val = data.get('educacion')
            independiente_val = data.get('independiente')
            historial_credito_val = data.get('historial_credito')
            zona_val = data.get('zona')

            genero_num = 1 if genero_val == "Masculino" else 0
            casado_num = 1 if casado_val == "Sí" else 0
            educacion_num = 1 if educacion_val == "Graduado" else 0
            independiente_num = 1 if independiente_val == "Sí" else 0
            historial_credito_num = 1 if historial_credito_val == "Sí" else 0

            dependientes_num = int(data.get('dependientes') or '0')

            zona_map = {"Rural": 0, "Semiurbano": 1, "Urbano": 2}
            zona_num = zona_map.get(zona_val if zona_val else "Rural", 0) 

            input_data = np.array([
                genero_num,
                casado_num,
                dependientes_num,
                educacion_num,
                independiente_num,
                float(data['ingreso_solicitante']),
                float(data['ingreso_cosolicitante']),
                float(data['monto_prestamo']),
                float(data['plazo_prestamo']),
                historial_credito_num,
                zona_num
            ]).reshape(1, -1)

            pred = model.predict(input_data)[0]
            resultado = "Crédito Aprobado" if pred == 1 else "Crédito Rechazado"

            # Guardar en DB
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO historial_predicciones (
                    genero, casado, dependientes, educacion, independiente,
                    ingreso_solicitante, ingreso_cosolicitante, monto_prestamo,
                    plazo_prestamo, historial_credito, zona, resultado_prediccion,
                    fecha, usuario_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                genero_val, casado_val, dependientes_num, educacion_val, independiente_val,
                float(data['ingreso_solicitante']), float(data['ingreso_cosolicitante']), float(data['monto_prestamo']),
                float(data['plazo_prestamo']), historial_credito_val, zona_val,
                resultado, datetime.datetime.now(), session['usuario_id']
            ))

            conn.commit()
            conn.close()
            flash(f"Predicción realizada: {resultado}") # Mensaje de éxito
        except Exception as e:
            print(f"Error en predicción: {e}")
            flash(f"Error en la predicción: {e}. Por favor, intenta de nuevo.")
            resultado = "Error en la predicción. Por favor, intenta de nuevo."

    return render_template('prediccion.html', usuario=session['usuario'], resultado=resultado)

# Historial
from flask_paginate import Pagination, get_page_args

@app.route('/historial')
@login_requerido
@role_requerido(['administrador', 'analista', 'usuario_basico'])
def historial():
    conn = conectar()
    rol = session.get('rol')
    
    # Configuración de paginación
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 10  # Número de items por página

    if rol and rol.lower() == 'usuario_basico':
        query = "SELECT * FROM historial_predicciones WHERE usuario_id = %s ORDER BY fecha DESC"
        count_query = "SELECT COUNT(*) FROM historial_predicciones WHERE usuario_id = %s"
        params = (session['usuario_id'],)
    else:
        query = "SELECT * FROM historial_predicciones ORDER BY fecha DESC"
        count_query = "SELECT COUNT(*) FROM historial_predicciones"
        params = ()

    # Obtener el total de registros
    total = pd.read_sql(count_query, conn, params=params).iloc[0,0]
    
    # Obtener datos paginados
    paginated_query = f"{query} LIMIT {per_page} OFFSET {offset}"
    df = pd.read_sql(paginated_query, conn, params=params)
    conn.close()

    # Renombrar columnas
    df = df.rename(columns={
        'id': 'ID', 'genero': 'Género', 'casado': 'Casado', 'dependientes': 'Dependientes', 
        'educacion': 'Educación', 'independiente': 'Independiente', 'ingreso_solicitante': 'Ingreso Solicitante', 
        'ingreso_cosolicitante': 'Ingreso Cosolicitante', 'monto_prestamo': 'Monto (S/)',
        'plazo_prestamo': 'Plazo (días)', 'historial_credito': 'Historial Crédito', 'zona': 'Zona',
        'resultado_prediccion': 'Resultado', 'fecha': 'Fecha'
    })

    # Formatear columnas
    df['Monto (S/)'] = df['Monto (S/)'].apply(lambda x: f"S/ {x:,.2f}")
    df['Ingreso Solicitante'] = df['Ingreso Solicitante'].apply(lambda x: f"S/ {x:,.2f}")
    df['Ingreso Cosolicitante'] = df['Ingreso Cosolicitante'].apply(lambda x: f"S/ {x:,.2f}")
    df['Fecha'] = pd.to_datetime(df['Fecha']).dt.strftime('%d/%m/%Y %H:%M')

    # Crear objeto de paginación
    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=total,
        css_framework='bootstrap5',
        record_name='predicciones'
    )

    return render_template(
        'historial.html',
        tablas=df.to_html(
            classes='table table-hover align-middle',
            index=False,
            border=0,
            justify='center',
            table_id='historial-table'
        ),
        pagination=pagination,
        usuario=session['usuario']
    )

#Descargar csv
@app.route('/descargar_csv')
@login_requerido
@role_requerido(['administrador', 'analista', 'usuario_basico']) 
def descargar_csv():
    conn = conectar()
    rol = session.get('rol')

    if rol and rol.lower() in ['administrador', 'analista']: 
        df = pd.read_sql("SELECT * FROM historial_predicciones ORDER BY fecha DESC", conn)
    else: 
        df = pd.read_sql("SELECT * FROM historial_predicciones WHERE usuario_id = %s ORDER BY fecha DESC",
                         conn, params=(session['usuario_id'],))
    conn.close()

    df = df.rename(columns={
        'id': 'ID', 'genero': 'Género', 'casado': 'Casado', 'dependientes': 'Dependientes', 
        'educacion': 'Educación', 'independiente': 'Independiente', 'ingreso_solicitante': 'Ingreso del Solicitante', 
        'ingreso_cosolicitante': 'Ingreso del Co-solicitante', 'monto_prestamo': 'Monto del Préstamo',
        'plazo_prestamo': 'Plazo del Préstamo', 'historial_credito': 'Historial de Crédito', 'zona': 'Zona',
        'resultado_prediccion': 'Resultado de Predicción', 'fecha': 'Fecha'
    })

    csv_data = df.to_csv(index=False, encoding='utf-8')
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=historial_predicciones.csv"}
    )

#Dashboard
@app.route('/dashboard')
@login_requerido
@role_requerido(['administrador', 'analista']) 
def dashboard():
    conn = conectar()
    rol = session.get('rol')
    usuario_id = session.get('usuario_id')

    if rol and (rol.lower() == 'administrador' or rol.lower() == 'analista'): 
        df_raw = pd.read_sql("SELECT * FROM historial_predicciones", conn)
    else:
        df_raw = pd.read_sql("SELECT * FROM historial_predicciones WHERE usuario_id = %s", conn, params=(usuario_id,))
    conn.close()

    total_solicitudes = len(df_raw)

    filtro_mes = request.args.get('filtro_mes')
    ver_grafico = request.args.get('ver_grafico')

    chart1 = None
    chart2 = None
    chart3 = None
    meses_disponibles = []

    if not df_raw.empty:
        df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
        df_raw['Año-Mes'] = df_raw['fecha'].dt.to_period('M').astype(str)
        df_raw['zona'] = df_raw['zona'].str.strip().str.capitalize()
        meses_disponibles = sorted(df_raw['Año-Mes'].unique())

    df_filtered = df_raw.copy()
    if filtro_mes:
        df_filtered = df_raw[df_raw['Año-Mes'] == filtro_mes]

    total_solicitudes_filtered = len(df_filtered)

    if not df_filtered.empty:
        if ver_grafico == 'solicitudes_mes' or not ver_grafico:
            df_solicitudes = df_filtered.groupby('Año-Mes').size().reset_index(name="Solicitudes")
            chart1 = px.bar(df_solicitudes, x='Año-Mes', y='Solicitudes', title="Solicitudes por mes")

        if ver_grafico == 'resultados' or not ver_grafico:
            df_resultados = df_filtered['resultado_prediccion'].value_counts().reset_index()
            df_resultados.columns = ['Resultado', 'Cantidad']
            chart2 = px.pie(df_resultados, names='Resultado', values='Cantidad', title="Resultados de las predicciones")

        if ver_grafico == 'zonas' or not ver_grafico:
            df_zonas = df_filtered['zona'].value_counts().reset_index()
            df_zonas.columns = ['Zona', 'Cantidad']
            chart3 = px.bar(df_zonas, x='Zona', y='Cantidad', title="Zonas de ubicación de propiedades")
    
    # Convertir los objetos de figura de Plotly a JSON strings
    chart1_json = json.dumps(chart1, cls=plotly.utils.PlotlyJSONEncoder) if chart1 is not None else 'null'
    chart2_json = json.dumps(chart2, cls=plotly.utils.PlotlyJSONEncoder) if chart2 is not None else 'null'
    chart3_json = json.dumps(chart3, cls=plotly.utils.PlotlyJSONEncoder) if chart3 is not None else 'null'

    return render_template(
        'dashboard.html',
        chart1=chart1_json, 
        chart2=chart2_json, 
        chart3=chart3_json, 
        total_solicitudes=total_solicitudes_filtered,
        meses_disponibles=meses_disponibles,
        filtro_seleccionado=filtro_mes,
        ver_grafico=ver_grafico,
        rol=rol
    )

# Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('usuario_id', None)
    session.pop('rol', None) 
    return redirect(url_for('inicio'))

# Ejecutar app
if __name__ == '__main__':
    app.run(debug=False)