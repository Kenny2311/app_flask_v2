from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.utils.autentication import login_requerido, encriptar

from app.models.usuarios_models import Usuario 
from app import db

import bcrypt
import re

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

#==============================================
#RUTAS
#==============================================
#Inicio
@auth_bp.route('/')
def home():
    return redirect(url_for('auth.menu_kfintech'))  # Redirige al menú si está disponible

#MENU
@auth_bp.route('/menu')
def menu():
    if 'usuario' in session:
        return render_template('menu.html', usuario=session['usuario'], rol=session.get('rol', ''), pagina_actual='menu')
    else:
        return render_template('inicio.html')

#INICIO
@auth_bp.route('/inicio')
def inicio():
    return render_template('inicio.html')

#LOGIN
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        try:
            user = Usuario.query.filter_by(correo=correo).first()
            if user and bcrypt.checkpw(contrasena.encode('utf-8'), user.contrasena.encode('utf-8')):
                session['usuario'] = correo
                session['usuario_id'] = user.id
                session['rol'] = user.rol.lower()
                session['nombres'] = user.nombres
                session['apellidos'] = user.apellidos
                session['correo'] = user.correo

                #quí guardamos el nombre completo
                session['nombre_completo'] = f"{user.nombres} {user.apellidos}"

                # Flash mensaje de bienvenida
                flash(f"¡Bienvenido de nuevo, {user.nombres.split()[0]}!", "success")

                return redirect(url_for('auth.inicio'))
            else:
                flash('Correo o contraseña incorrectos', "danger")

        except Exception as e:
            flash(f"Error al iniciar sesión: {str(e)}", "danger")

    return render_template('login.html')



#REGISTRO
@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Extracción de datos
        nombres = request.form['nombres']
        apellidos = request.form['apellidos']
        dni = request.form['dni']
        correo = request.form['correo']
        celular = request.form['celular']
        genero = request.form['genero']
        #usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        rol = 'usuario_basico'

        if contrasena != confirmar_contrasena or not re.search(r'[A-Za-z]', contrasena) or not re.search(r'\d', contrasena):
            flash("La contraseña debe contener letras y números, y coincidir.")
            return render_template('registro.html')

        contrasena_encriptada = encriptar(contrasena)

        try:
            if Usuario.query.filter_by(dni=dni).first():
                flash("El DNI ya está registrado.", "danger")
                return render_template('registro.html')

            # Validar correo único
            if Usuario.query.filter_by(correo=correo).first():
                flash("El correo ya está registrado.", "danger")
                return render_template('registro.html')
            
            # Crear usuario nuevo
            nuevo_usuario = Usuario(
                contrasena=contrasena_encriptada,
                rol=rol,
                nombres=nombres,
                apellidos=apellidos,
                dni=dni,
                correo=correo,
                celular=celular,
                genero=genero
            )

            db.session.add(nuevo_usuario)
            db.session.commit()

            flash("Registro exitoso. ¡Bienvenido!", "success")
            return redirect(url_for('auth.login'))

        except Exception as e:
            flash(f"Error al registrar usuario: {str(e)}", "danger")

    return render_template('registro.html')


################################################################
# AQUI CREAREMOS LA NUEVA OPCION DE IR A PLATAFORMA K-FINTECH
@auth_bp.route('/menu_kfintech')
def menu_kfintech():
    if 'correo' not in session:
        return redirect(url_for('auth.login'))

    return render_template(
        'menu_kfintech.html',
        usuario=session['usuario'],
        rol=session.get('rol', ''),
        nombre_usuario=session.get('nombre_completo', session.get('usuario', 'Usuario')),
        pagina_actual='menu_kfintech',       # 👈🔥 IMPORTANTE
        active_page='menu_kfintech'          # Opcional si quieres resaltar en sidebar
    )
################################################################


# CERRAR SESIÓN
@auth_bp.route('/logout')
def logout():
    session.clear()   # 🔥 Borra TODA la sesión de forma segura

    # ✅ Flash mensaje de cierre de sesión
    flash("¡Hasta luego! Esperamos verte pronto de nuevo.", "info")

    return redirect(url_for('auth.inicio'))