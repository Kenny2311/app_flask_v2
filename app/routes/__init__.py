from .auth_routes import auth_bp
from .asistente_routes import asistente_bp
from app.routes.prediccion_routes import prediccion_bp
from app.routes.historial_routes import historial_bp
from app.routes.dashboard_routes import dashboard_bp
from app.routes.usuarios_routes import usuarios_bp
from app.routes.roles_routes import roles_bp
from app.routes.estado_modelo_routes import estado_modelo_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(asistente_bp)
    app.register_blueprint(prediccion_bp)
    app.register_blueprint(historial_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(usuarios_bp)  
    app.register_blueprint(roles_bp) 
    app.register_blueprint(estado_modelo_bp)