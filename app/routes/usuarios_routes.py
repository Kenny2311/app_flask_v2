from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from app.utils.autentication import login_requerido, encriptar
from app.utils.autentication import role_requerido
import bcrypt
import re

from app.models.usuarios_models import Usuario
from app import db

usuarios_bp = Blueprint('usuarios', __name__, template_folder='../templates')


#VERIFICAR DNI
@usuarios_bp.route('/verificar_dni', methods=['POST'])
def verificar_dni():
    dni = request.json.get('dni')
    existe = Usuario.query.filter_by(dni=dni).first() is not None
    return jsonify({'existe': existe})




#IR A MENU DE PERFIL
@usuarios_bp.route('/menu_perfil')
@login_requerido
def menu_perfil():
    usuario_correo = session.get('usuario')
    try:
        usuario = Usuario.query.filter_by(correo=usuario_correo).first()
        if usuario:
             return render_template('menu_perfil.html', usuario=usuario)
        else:
            flash("Nose pudo acceder al menu del perfil.", "Danger")
            return redirect(url_for('auth.inicio'))
    
    except Exception as e:
        print(f"[ERROR PERFL] {str(e)}")
        flash(f"Error al cargar menu del perfil:{str(e)}", "danger")
        return redirect(url_for('auth.inicio')) 



# EDITAR PERFIL
@usuarios_bp.route('/datos_personales', methods=['GET', 'POST'])
@login_requerido
def datos_personales():
    usuario_correo = session.get('usuario')
    usuario = Usuario.query.filter_by(correo=usuario_correo).first()

    if not usuario:
        flash("No se encontró el usuario.", "danger")
        return redirect(url_for('usuarios.datos_personales'))

    if request.method == 'POST':
        usuario.nombres = request.form['nombres']
        usuario.apellidos = request.form['apellidos']

        # Si cambia el correo, también se debe actualizar la sesión
        nuevo_correo = request.form['correo']
        usuario.correo = nuevo_correo
        usuario.celular = request.form['celular']

        try:
            db.session.commit()
            # Actualizar sesión si el usuario cambió su correo
            session['usuario'] = nuevo_correo

            flash("Perfil actualizado correctamente.", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar perfil: {str(e)}", "danger")

        return redirect(url_for('usuarios.datos_personales'))

    return render_template('datos_personales.html', usuario=usuario, active_page='datos_personales')


# CAMBIAR CONTRASEÑA
@usuarios_bp.route('/cambiar_contrasena', methods=['GET', 'POST'])
@login_requerido
def cambiar_contrasena():
    usuario_correo = session.get('usuario')
    usuario = Usuario.query.filter_by(correo=usuario_correo).first()

    if not usuario:
        return jsonify({"success": False, "message": "Usuario no encontrado."})

    if request.method == 'POST':
        actual = request.form.get('actual')
        nueva = request.form.get('nueva')
        confirmar = request.form.get('confirmar')

        if not actual or not nueva or not confirmar:
            return jsonify({"success": False, "message": "Debes completar todos los campos."})

        if not bcrypt.checkpw(actual.encode('utf-8'), usuario.contrasena.encode('utf-8')):
            return jsonify({"success": False, "message": "La contraseña actual es incorrecta."})

        if nueva != confirmar:
            return jsonify({"success": False, "message": "Las contraseñas no coinciden."})

        if nueva == actual:
            return jsonify({"success": False, "message": "La nueva contraseña no puede ser igual a la actual."})

        if not re.search(r'[A-Za-z]', nueva) or not re.search(r'\d', nueva):
            return jsonify({"success": False, "message": "La contraseña debe contener al menos una letra y un número."})

        usuario.contrasena = encriptar(nueva)
        try:
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"Error al cambiar contraseña: {str(e)}"})

    # Si es GET, renderizamos el formulario
    return render_template(
        'cambiar_contrasena.html', 
        usuario=usuario, 
        active_page='cambiar_contrasena'
    )



# CAMBIAR CORREO
@usuarios_bp.route('/cambiar_correo', methods=['GET', 'POST'])
@login_requerido
def cambiar_correo():
    usuario_correo = session.get('usuario')
    usuario = Usuario.query.filter_by(correo=usuario_correo).first()

    if not usuario:
        return jsonify({"success": False, "message": "Usuario no encontrado."})

    if request.method == 'POST':
        nuevo_correo = request.form.get('nuevo_correo')
        contrasena_actual = request.form.get('contrasena_actual_correo')

        if not nuevo_correo or not contrasena_actual:
            return jsonify({"success": False, "message": "Debes completar todos los campos."})

        # Validar contraseña actual
        if not bcrypt.checkpw(contrasena_actual.encode('utf-8'), usuario.contrasena.encode('utf-8')):
            return jsonify({"success": False, "message": "La contraseña actual es incorrecta."})

        # Actualizar correo y sesión
        usuario.correo = nuevo_correo
        try:
            db.session.commit()
            session['usuario'] = nuevo_correo
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"Error al cambiar correo: {str(e)}"})

    # Si es GET, renderizamos el formulario
    return render_template(
        'cambiar_correo.html', 
        usuario=usuario, 
        active_page='cambiar_correo'
    )




# ELIMINAR PERFIL
@usuarios_bp.route('/eliminar_perfil', methods=['GET', 'POST'])
@login_requerido
def eliminar_perfil():
    usuario_correo = session.get('usuario')
    usuario = Usuario.query.filter_by(correo=usuario_correo).first()

    if not usuario:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for('usuarios.datos_personales'))

    if request.method == 'POST':
        # Esto ahora acepta JSON o form-data
        if request.is_json:
            data = request.get_json()
            contrasena = data.get('contrasena')
            motivo = data.get('motivo')
        else:
            contrasena = request.form.get('contrasena')
            motivo = request.form.get('motivo')

        if not contrasena:
            return jsonify({"success": False, "message": "Debes ingresar tu contraseña."})

        if not bcrypt.checkpw(contrasena.encode('utf-8'), usuario.contrasena.encode('utf-8')):
            return jsonify({"success": False, "message": "Contraseña incorrecta."})

        try:
            db.session.delete(usuario)
            db.session.commit()
            session.clear()
            return jsonify({"success": True, "message": "Perfil eliminado correctamente."})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"Error al eliminar perfil: {str(e)}"})

    # GET → renderizamos la página normalmente
    return render_template(
        'eliminar_perfil.html',
        usuario=usuario,
        active_page='eliminar_perfil'
    )
