import joblib
import os

# Construir la ruta al modelo básico
modelo_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'modelo_basico.pkl')

# Cargar el modelo con joblib
modelo_basico = joblib.load(modelo_path)

def predecir_con_modelo_basico(datos_np):
    """
    datos_np: numpy array con los campos que usa el modelo básico
    """
    # Probabilidad de clase positiva
    proba = modelo_basico.predict_proba(datos_np)[0][1]

    # Clasificación de riesgo según probabilidad
    riesgo = (
        "ALTO RIESGO" if proba > 0.6 else
        "RIESGO MODERADO" if proba > 0.3 else
        "BAJO RIESGO"
    )
    
    return round(proba * 100, 2), riesgo