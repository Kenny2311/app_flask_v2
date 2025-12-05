from functools import wraps
from flask import session, redirect, url_for
import bcrypt
import joblib

def encriptar(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def login_requerido(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if 'usuario' not in session or 'usuario_id' not in session or 'rol' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorada


def role_requerido(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get('rol', '').lower() 
            lower_allowed_roles = [role.lower() for role in allowed_roles]

            print("ROL ACTUAL:", user_role)
            print("ROLES PERMITIDOS:", lower_allowed_roles)

            if user_role not in lower_allowed_roles:
                return "Acceso denegado: No tienes permiso para ver esta página.", 403 
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def load_model():
    try:
        model = joblib.load('modelo_xgb.pkl')
        print("Modelo cargado correctamente.")
        return model
    except:
        print("Error al cargar el modelo.")
        return None
