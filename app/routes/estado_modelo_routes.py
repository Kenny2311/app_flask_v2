from flask import Blueprint, render_template, request, send_file, session
import os

from app.utils.autentication import login_requerido
from app.utils.autentication import role_requerido

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="xgboost")

import io
from reportlab.pdfgen import canvas
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


estado_modelo_bp = Blueprint('modelo', __name__, template_folder='../templates')

# Ruta EXACTA del modelo como en prediccion
modelo_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'modelo_xgb.pkl')

if not os.path.exists(modelo_path) or not os.path.exists('app/models/X_test.pkl') or not os.path.exists('app/models/y_test.pkl'):
    raise FileNotFoundError("Modelo o archivos de test no encontrados")





# ESTADO DEL MODELO - RENDIMIENTO (HU028, HU029)
@estado_modelo_bp.route('/estado_modelo_rendimiento')
@login_requerido
@role_requerido(['administrador', 'analista'])
def estado_modelo_rendimiento():
    try:
        # Cargar modelo
        modelo_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'modelo_xgb.pkl')
        modelo = joblib.load(modelo_path)

        # Cargar datos de prueba
        X_test = joblib.load('app/models/X_test.pkl')
        y_test = joblib.load('app/models/y_test.pkl')

        # Predicciones
        y_pred = modelo.predict(X_test)

        # Calcular métricas
        accuracy = round(accuracy_score(y_test, y_pred), 4)
        precision = round(precision_score(y_test, y_pred), 4)
        recall = round(recall_score(y_test, y_pred), 4)
        f1 = round(f1_score(y_test, y_pred), 4)

        metricas = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }

        # Alertas de rendimiento bajo
        alerta = accuracy < 0.70
        error_metricas = None

        # Datos del modelo solo si es administrador
        datos = None
        if session.get('rol') == 'administrador':
            datos = {
                "algoritmo": "XGBoost Classifier",
                "version": modelo.get_params().get("n_estimators", "1.0"),
                "fecha_entrenamiento": "2025-01-15",
                "features_usadas": list(X_test.columns)
            }

    except Exception as e:
        print("ERROR OBTENIENDO MÉTRICAS:", e)
        metricas = None
        alerta = None
        error_metricas = "Error al obtener las métricas del modelo."
        datos = None

    return render_template(
        'estado_modelo_rendimiento.html',
        metricas=metricas,
        alerta=alerta,
        error_metricas=error_metricas,
        datos=datos,  # Ahora siempre existe (puede ser None)
        rol=session.get('rol'),  # 🔥 Añadir rol aquí
        active_page='estado_modelo_rendimiento',
    )






# ESTADO DEL MODELO - SOLO DATOS
@estado_modelo_bp.route('/estado_modelo_datos')
@login_requerido
@role_requerido(['administrador'])
def estado_modelo_datos():
    try:
        # Ruta del modelo
        modelo_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'modelo_xgb.pkl')
        modelo = joblib.load(modelo_path)

        # Cargar datos reales del test
        X_test = joblib.load('app/models/X_test.pkl')
        y_test = joblib.load('app/models/y_test.pkl')

        # Predicciones del modelo
        y_pred = modelo.predict(X_test)

        # Calcular métricas
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        metricas = {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4)
        }

        # Datos del modelo (siempre visibles aquí)
        datos = None
        if session.get('rol') == 'administrador':
            datos = {
                "algoritmo": "XGBoost Classifier",
                "version": modelo.get_params().get("n_estimators", "1.0"),
                "fecha_entrenamiento": "2025-01-15",
                "features_usadas": list(X_test.columns)
            }

        error_metricas = None

    except Exception as e:
        print("ERROR OBTENIENDO MÉTRICAS:", e)
        metricas = None
        datos = None
        error_metricas = "Error al obtener las métricas del modelo. Intente nuevamente."

    # Alerta si el modelo cae debajo del umbral
    rendimiento_actual = metricas["accuracy"] if metricas else 0
    umbral_minimo = 0.70
    alerta = rendimiento_actual < umbral_minimo

    return render_template(
        'estado_modelo_datos.html',  # <-- template separado para solo datos
        metricas=metricas,
        datos=datos,
        alerta=alerta,
        rendimiento=rendimiento_actual,
        umbral=umbral_minimo,
        error_metricas=error_metricas,
        rol=session.get('rol'),  # 🔥 Añadir rol aquí
        active_page='estado_modelo_datos'       
    )






# Descargar reporte PDF del estado del modelo (HU030)
@estado_modelo_bp.route('/descargar_reporte')
@login_requerido
@role_requerido(['administrador', 'analista'])
def descargar_reporte():
    # Inicializar métricas por si falla la carga
    accuracy = precision = recall = f1 = "N/A"
    n_estimators = "N/A"

    try:
        # Cargar modelo y datos de prueba
        modelo_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'modelo_xgb.pkl')
        modelo = joblib.load(modelo_path)
        X_test = joblib.load(os.path.join('app', 'models', 'X_test.pkl'))
        y_test = joblib.load(os.path.join('app', 'models', 'y_test.pkl'))

        # Predicciones y métricas
        y_pred = modelo.predict(X_test)
        accuracy = round(accuracy_score(y_test, y_pred), 4)
        precision = round(precision_score(y_test, y_pred), 4)
        recall = round(recall_score(y_test, y_pred), 4)
        f1 = round(f1_score(y_test, y_pred), 4)
        n_estimators = modelo.get_params().get('n_estimators', 'N/A')

    except Exception as e:
        print("ERROR GENERANDO PDF:", e)

    # Crear PDF en memoria
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, "Resumen del Modelo Predictivo")
    p.drawString(100, 780, f"Algoritmo: XGBoost")
    p.drawString(100, 760, f"Número de estimadores: {n_estimators}")
    p.drawString(100, 740, f"Fecha Entrenamiento: 2025-01-15")
    p.drawString(100, 720, f"Accuracy: {accuracy}")
    p.drawString(100, 700, f"Precision: {precision}")
    p.drawString(100, 680, f"Recall: {recall}")
    p.drawString(100, 660, f"F1 Score: {f1}")
    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte_modelo.pdf",
        mimetype="application/pdf"
    )