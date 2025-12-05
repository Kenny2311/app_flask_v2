#Init_ de app

from flask import Flask
from app.extensions import db 
import os

from config import Config

def create_app():

    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), 'static'),
        template_folder=os.path.join(os.path.dirname(__file__), 'templates')
        )

    app.config.from_object(Config)


    # Inicializa la base de datos con Flask
    db.init_app(app)

    # Importa y registra tus rutas (si ya tienes blueprints)
    from app.routes.auth_routes import auth_bp
    from app.routes.asistente_routes import asistente_bp
    from app.routes.prediccion_routes import prediccion_bp
    from app.routes.historial_routes import historial_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.usuarios_routes import usuarios_bp
    from app.routes.roles_routes import roles_bp
    from app.routes.enviar_codigo_routes import enviar_codigo_bp
    from app.routes.estado_modelo_routes import estado_modelo_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(asistente_bp)
    app.register_blueprint(prediccion_bp)
    app.register_blueprint(historial_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(enviar_codigo_bp)
    app.register_blueprint(estado_modelo_bp)


    return app
