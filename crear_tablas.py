# crear_tablas.py

from app import create_app
from app.extensions import db
from app.models.prediccion_models import Prediccion  # ajusta el path si hace falta

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ Tablas creadas correctamente.")