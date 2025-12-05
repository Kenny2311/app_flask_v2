from datetime import datetime
from app.extensions import db

class PrediccionBasico(db.Model):
    __tablename__ = 'prediccion_basico'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False)

    # Información del solicitante (informativa para historial, no usada en predicción)
    nombre_solicitante = db.Column(db.String(100), nullable=False)
    genero = db.Column(db.String(20))
    casado = db.Column(db.String(10))
    dependientes = db.Column(db.Integer)
    educacion = db.Column(db.String(50))
    zona_propiedad = db.Column(db.String(50))

    # Datos financieros usados para la predicción
    Edad = db.Column(db.Integer)
    Ingreso_Anual = db.Column(db.Float)
    Salario_Mensual_Mano = db.Column(db.Float)
    Nro_Cuentas_Bancarias = db.Column(db.Integer)
    Nro_Tarjetas_Credito = db.Column(db.Integer)
    Deuda_Pendiente = db.Column(db.Float)
    Tipo_Prestamo = db.Column(db.Integer)  # 0=personal, 1=hipotecario...
    Monto_Invertido_Mensualmente = db.Column(db.Float)
    Tasa_Interes = db.Column(db.Float)

    # Metadatos de la predicción
    fecha_prediccion = db.Column(db.DateTime, default=datetime.utcnow)
    modelo_version = db.Column(db.String(50), default="v1.0_basico")
    estado_prediccion = db.Column(db.String(20))  # EXITO | ERROR
    probabilidad_default = db.Column(db.Float)  # Probabilidad predicción
    nivel_riesgo = db.Column(db.String(20))  # Bajo, Medio, Alto

    def __repr__(self):
        return f'<PrediccionBasico {self.id} - {self.nombre_solicitante}>'
