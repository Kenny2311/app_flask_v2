from app.extensions import db 

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    contrasena = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(8), nullable=False, unique=True)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    celular = db.Column(db.String(9), nullable=False)
    genero = db.Column(db.String(10), nullable=False)

def __repr__(self):
    return f"<Usuario {self.correo}>"   