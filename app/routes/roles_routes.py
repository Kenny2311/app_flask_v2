from flask import Blueprint, request, redirect, url_for, flash, session, render_template

from app.utils.autentication import login_requerido
from app.utils.autentication import role_requerido

from app.models.usuarios_models import Usuario
from app import db



roles_bp = Blueprint('roles', __name__, template_folder='../templates')


#Listar usuarios
@roles_bp.route('/listar_usuarios')
@login_requerido
@role_requerido(['administrador'])
def listar_usuarios():
    try:
        # Administrador principal
        admin_usuario = Usuario.query.with_entities(
            Usuario.dni, Usuario.correo, Usuario.rol, Usuario.nombres, Usuario.apellidos
        ).filter(Usuario.rol == 'administrador').first()


        # Usuarios que no son administradores
        usuarios_normales = Usuario.query.with_entities(
            Usuario.dni, Usuario.correo, Usuario.rol, Usuario.nombres, Usuario.apellidos
        ).filter(Usuario.rol != 'administrador').order_by(Usuario.apellidos.asc(), Usuario.nombres.asc()).all()


        # Totales
        total_usuarios = Usuario.query.count()
        total_administradores = Usuario.query.filter_by(rol='administrador').count()
        total_analistas = Usuario.query.filter_by(rol='analista').count()
        total_basicos = Usuario.query.filter_by(rol='usuario_basico').count()

        return render_template(
            'gestion_roles.html',
            admin_usuario=admin_usuario,
            usuarios=usuarios_normales,
            usuario=session.get('usuario'),
            rol=session.get('rol'),  # <- esto es clave para el menú
            active_page='listar_usuarios',
            total_usuarios=total_usuarios,
            total_administradores=total_administradores,
            total_analistas=total_analistas,
            total_basicos=total_basicos
        )
    except Exception as e:
        print(f"[ERROR LISTAR USUARIOS] {str(e)}")
        flash(f"Error al listar usuarios: {str(e)}", "danger")
        return redirect(url_for('auth.menu_kfintech'))



# CAMBIAR ROL
@roles_bp.route('/cambiar_rol/<string:id>', methods=['POST'])
@login_requerido
@role_requerido(['administrador'])
def cambiar_rol(id):
    nuevo_rol = request.form.get('rol')
    if not nuevo_rol:
        flash('No se recibió el nuevo rol.', 'danger')
        return redirect(url_for('roles.listar_usuarios'))

    try:
        usuario = Usuario.query.filter_by(dni=id).first()
        if usuario:
            usuario.rol = nuevo_rol
            db.session.commit()
            nombre_completo = f"{usuario.nombres} {usuario.apellidos}" if usuario.nombres and usuario.apellidos else usuario.correo
            flash(f'Rol actualizado correctamente para {nombre_completo}.', 'success')
        else:
            flash('Usuario no encontrado.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar el rol: {str(e)}', 'danger')

    return redirect(url_for('roles.listar_usuarios'))




# ELIMINAR USUARIO
@roles_bp.route('/eliminar_usuario/<int:id>', methods=['POST'])
@login_requerido
@role_requerido(['administrador'])
def eliminar_usuario(id):
    try:
        usuario = Usuario.query.get(id)
        if usuario:
            db.session.delete(usuario)
            db.session.commit()
            flash('Usuario eliminado correctamente', 'success')
        else:
            flash('Usuario no encontrado', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el usuario: {str(e)}', 'danger')
    
    return redirect(url_for('roles.listar_usuarios'))