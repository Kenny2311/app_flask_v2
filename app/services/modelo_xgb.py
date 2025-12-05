import joblib

# Carga el modelo con joblib
modelo = joblib.load('app/modelos/modelo_xgb.pkl')

def predecir_con_modelo_xgb(datos_np):
    proba = modelo.predict_proba(datos_np)[0][1]  # Probabilidad clase positiva
    riesgo = "ALTO RIESGO" if proba > 0.6 else "RIESGO MODERADO" if proba > 0.3 else "BAJO RIESGO"
    return round(proba * 100, 2), riesgo