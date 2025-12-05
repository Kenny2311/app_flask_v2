import joblib
from app.extensions import db
import numpy as np

modelo = joblib.load('app/models/modelo_xgb.pkl')

def predecir_datos(input_data_dict):
    columnas_ordenadas = ['Edad', 'Ocupacion', 'Ingreso_Anual', 'Salario_Mensual_Mano', 
                          'Nro_Cuentas_Bancarias', 'Nro_Tarjetas_Credito', 'Tasa_Interes', 
                          'Nro_Prestamos', 'Tipo_Prestamo', 'Cambio_Limite_Credito', 
                          'Nro_Consultas_Credito', 'Deuda_Pendiente', 'Ratio_Utilizacion_Credito', 
                          'Antiguedad_Historial_Credito', 'EMI_Total_Mensual', 'Monto_Invertido_Mensualmente',
                          'Puntaje_Credito', 'Ratio_Deuda_Ingreso', 'Ratio_EMI_Ingreso', 'Ahorro_Mensual', 
                          'Sector_Economico', 
                          'Infocorp_Flag', 'Region']  # Asegúrate de respetar el orden correcto
    datos_input = np.array([[input_data_dict[col] for col in columnas_ordenadas]])
    
    probabilidad = modelo.predict_proba(datos_input)[0][1]
    riesgo = 'Alto' if probabilidad > 0.5 else 'Bajo'
    
    return probabilidad, riesgo
