from datetime import datetime
from app.extensions import db

class Prediccion(db.Model):
    __tablename__ = 'prediccion'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False)

    # Información del solicitante
    dni_solicitante = db.Column(db.String(20), nullable=False)
    nombre_solicitante = db.Column(db.String(100), nullable=False)

    # Metadatos de la predicción
    fecha_prediccion = db.Column(db.DateTime, default=datetime.utcnow)
    modelo_version = db.Column(db.String(50), default="v1.0")
    estado_prediccion = db.Column(db.String(20))  # EXITO | ERROR
    tiempo_inferencia_ms = db.Column(db.Float)

    # Resultados del modelo
    probabilidad_default = db.Column(db.Float)  # PD
    nivel_riesgo = db.Column(db.String(20))  # Bajo, Medio, Alto
    variables_importantes = db.Column(db.Text)  # JSON con top features (SHAP)

    # Campos para la predicicion
    Edad = db.Column(db.Integer)
    Ocupacion = db.Column(db.String(100))
    Ingreso_Anual = db.Column(db.Float)
    Salario_Mensual_Mano = db.Column(db.Float)
    Nro_Cuentas_Bancarias = db.Column(db.Integer)
    Nro_Tarjetas_Credito = db.Column(db.Integer)
    Tasa_Interes = db.Column(db.Float)
    Nro_Prestamos = db.Column(db.Integer)
    Tipo_Prestamo = db.Column(db.String(100))
    Cambio_Limite_Credito = db.Column(db.Float)
    Nro_Consultas_Credito = db.Column(db.Integer)
    Deuda_Pendiente = db.Column(db.Float)
    Ratio_Utilizacion_Credito = db.Column(db.Float)
    Antiguedad_Historial_Credito = db.Column(db.Float)
    EMI_Total_Mensual = db.Column(db.Float)
    Monto_Invertido_Mensualmente = db.Column(db.Float)
    Puntaje_Credito = db.Column(db.Float)
    Ratio_Deuda_Ingreso = db.Column(db.Float)
    Ratio_EMI_Ingreso = db.Column(db.Float)
    Ahorro_Mensual = db.Column(db.Float)
    Sector_Economico = db.Column(db.String(100))
    Infocorp_Flag = db.Column(db.Integer)
    Region = db.Column(db.String(100))