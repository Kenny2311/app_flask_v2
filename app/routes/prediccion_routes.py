from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from app.utils.autentication import login_requerido
from app.utils.autentication import role_requerido
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

import xgboost as xgb

from app.models.prediccion_models import Prediccion
from app.models.prediccion_basico_models import PrediccionBasico
from app import db

from app.utils.mapeos import OCUPACION_MAP, TIPO_PRESTAMO_MAP, SECTOR_ECONOMICO_MAP, REGION_MAP

prediccion_bp = Blueprint('prediccion', __name__, template_folder='../templates')



# ========================
# MODELOS
# ========================

# Ruta de modelo predictivo (analistas / administradores)
modelo_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'modelo_xgb.pkl')
modelo_xgb = joblib.load(modelo_path)


# Ruta de modelo predictivo (usuarios básicos)
modelo_basico_path = os.path.join(os.path.dirname(__file__), '..', 'models', "modelo_basico.pkl")
modelo_basico = joblib.load(modelo_basico_path)



# PREDICCION
@prediccion_bp.route('/prediccion', methods=['GET', 'POST'])
@login_requerido
@role_requerido(['administrador', 'analista']) 
def prediccion():   
    if request.method == 'POST':
        
        try:
            # Obtener datos del formulario
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()

            input_data = pd.DataFrame([data])

            # Capturar los campos adicionales (no usados por el modelo)
            nombre_solicitante = data.get('nombre_solicitante')
            fecha_prediccion_str = data.get('fecha_prediccion') # formato esperado: 'dd/mm/aaaa'

            # Convertir fecha a datetime
            try:
                # Convertimos a datetime y luego solo tomamos la fecha
                fecha_prediccion = datetime.strptime(fecha_prediccion_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                fecha_prediccion = datetime.utcnow().date()  # fecha actual sin hora

            # Convertir Infocorp a binario
            data['Infocorp_Flag'] = 1 if 'Infocorp_Flag' in data else 0

            # Mantener valores string
            campos_string = ['Ocupacion', 'Tipo_Prestamo', 'Sector_Economico', 'Region']

            # Convertir valores numéricos
            campos_numericos = [
                'Edad', 'Ingreso_Anual', 'Salario_Mensual_Mano', 'Nro_Cuentas_Bancarias',
                'Nro_Tarjetas_Credito', 'Tasa_Interes', 'Nro_Prestamos', 'Cambio_Limite_Credito',
                'Nro_Consultas_Credito', 'Deuda_Pendiente', 'Ratio_Utilizacion_Credito',
                'Antiguedad_Historial_Credito', 'EMI_Total_Mensual', 'Monto_Invertido_Mensualmente',
                 'Puntaje_Credito','Ratio_Deuda_Ingreso', 'Ratio_EMI_Ingreso',
                'Ahorro_Mensual'
            ]


            # Guardamos los valores legibles originales en variables
            ocupacion_str = OCUPACION_MAP.get(data['Ocupacion'], "Desconocido")
            tipo_prestamo_str = TIPO_PRESTAMO_MAP.get(data['Tipo_Prestamo'], "Desconocido")
            sector_economico_str = SECTOR_ECONOMICO_MAP.get(data['Sector_Economico'], "Desconocido")
            region_str = REGION_MAP.get(data['Region'], "Desconocido")


            for campo in campos_numericos:
                try:
                    data[campo] = float(data[campo])
                except ValueError:
                    flash(f'Campo inválido: {campo}', 'danger')
                    return redirect(url_for('prediccion.prediccion'))


            # También los string, pero para el modelo, si los usas como números
            data['Ocupacion'] = float(data['Ocupacion'])
            data['Tipo_Prestamo'] = float(data['Tipo_Prestamo'])
            data['Sector_Economico'] = float(data['Sector_Economico'])
            data['Region'] = float(data['Region'])


            # Validaciones de campos obligatorios
            campos_obligatorios = ['nombre_solicitante', 'Edad', 'Ingreso_Anual', 'Salario_Mensual_Mano', 'Puntaje_Credito']
            for campo in campos_obligatorios:
                if not data.get(campo):
                    flash(f'El campo "{campo}" es obligatorio.', 'danger')
                    return redirect(url_for('prediccion.prediccion'))

            # Preparar datos para predicción (ajusta el orden según entrenaste tu modelo)
            input_data = np.array([[
                data['Edad'],
                data['Ocupacion'], 
                data['Ingreso_Anual'], 
                data['Salario_Mensual_Mano'],
                data['Nro_Cuentas_Bancarias'], 
                data['Nro_Tarjetas_Credito'], 
                data['Tasa_Interes'],
                data['Nro_Prestamos'],
                data['Tipo_Prestamo'], 
                data['Cambio_Limite_Credito'], 
                data['Nro_Consultas_Credito'],
                data['Deuda_Pendiente'], 
                data['Ratio_Utilizacion_Credito'], 
                data['Antiguedad_Historial_Credito'],
                data['EMI_Total_Mensual'], 
                data['Monto_Invertido_Mensualmente'], 
                data['Puntaje_Credito'],
                data['Ratio_Deuda_Ingreso'], 
                data['Ratio_EMI_Ingreso'], 
                data['Ahorro_Mensual'],
                data['Sector_Economico'],
                data['Infocorp_Flag'],
                data['Region']
            ]])

            # Medir tiempo de inferencia
            inicio = datetime.utcnow()

            # Realizar la predicción
            resultado = modelo_xgb.predict(input_data)[0]
            
            try:
                probabilidad = float(modelo_xgb.predict_proba(input_data)[0][1])  # Probabilidad de clase 1 (riesgo alto)
            except:
                probabilidad = float(resultado)  # En caso no esté disponible, usamos 0 o 1 directamente

            fin = datetime.utcnow()
            tiempo_inferencia = (fin - inicio).total_seconds() * 1000  # ms

            # Clasificación de riesgo según la probabilidad
            if probabilidad >= 0.70:
                riesgo = "ALTO"
            elif probabilidad >= 0.30:
                riesgo = "MEDIO"
            else:
                riesgo = "BAJO"

            # SHAP (opcional)
            variables_importantes_json = "{}"

            # Validar usuario
            usuario_id = session.get('usuario_id')
            if not usuario_id:
                flash('Usuario no autenticado.', 'danger')
                return redirect(url_for('auth.login'))  

            # GUARDAR PREDICCIÓN COMPLETA
            nueva_prediccion = Prediccion(
                usuario_id=session['usuario_id'],

                # Información del solicitante
                dni_solicitante=data.get('dni_solicitante'),
                nombre_solicitante=nombre_solicitante,

                # Metadatos del sistema
                fecha_prediccion=datetime.utcnow().date(),
                modelo_version="v1.0",
                estado_prediccion="EXITO",
                tiempo_inferencia_ms=tiempo_inferencia,

                # Resultados del modelo
                probabilidad_default=probabilidad,
                nivel_riesgo=riesgo,
                 variables_importantes="{}",

                # Campos del formulario
                Edad=data['Edad'],
                Ocupacion=ocupacion_str,
                Ingreso_Anual=data['Ingreso_Anual'],
                Salario_Mensual_Mano=data['Salario_Mensual_Mano'],
                Nro_Cuentas_Bancarias=data['Nro_Cuentas_Bancarias'],
                Nro_Tarjetas_Credito=data['Nro_Tarjetas_Credito'],
                Tasa_Interes=data['Tasa_Interes'],
                Nro_Prestamos=data['Nro_Prestamos'],
                Tipo_Prestamo=tipo_prestamo_str,
                Cambio_Limite_Credito=data['Cambio_Limite_Credito'],
                Nro_Consultas_Credito=data['Nro_Consultas_Credito'],
                Deuda_Pendiente=data['Deuda_Pendiente'],
                Ratio_Utilizacion_Credito=data['Ratio_Utilizacion_Credito'],
                Antiguedad_Historial_Credito=data['Antiguedad_Historial_Credito'],
                EMI_Total_Mensual=data['EMI_Total_Mensual'],
                Monto_Invertido_Mensualmente=data['Monto_Invertido_Mensualmente'],
                Puntaje_Credito=data['Puntaje_Credito'],
                Ratio_Deuda_Ingreso=data['Ratio_Deuda_Ingreso'],
                Ratio_EMI_Ingreso=data['Ratio_EMI_Ingreso'],
                Ahorro_Mensual=data['Ahorro_Mensual'],
                Sector_Economico=sector_economico_str,
                Infocorp_Flag=data['Infocorp_Flag'],
                Region=region_str
            )

            print("DATOS RECIBIDOS:", data)
            print("Resultado de predicción:", resultado)
            print("Usuario ID:", session.get('usuario_id'))

            db.session.add(nueva_prediccion)
            db.session.commit()


            print(f"Usuario ID: {session.get('usuario_id')}, Resultado: {resultado}, Probabilidad: {probabilidad}")

            flash('Predicción realizada y guardada correctamente.', 'success')

            flash(f'Predicción realizada: {resultado}', 'success')


            # Mensaje personalizado según riesgo
            if riesgo == "ALTO":
                mensaje_personalizado = (
                    "El solicitante presenta un riesgo ALTO de impago. "
                    "Se recomienda no aprobar el crédito o limitarlo a un monto pequeño."
                )
                monto_recomendado = 2500

            elif riesgo == "MEDIO":
                mensaje_personalizado = (
                    "El solicitante presenta un riesgo MEDIO. "
                    "Se recomienda otorgar un monto moderado bajo supervisión."
                )
                monto_recomendado = 6000

            else:  # BAJO
                mensaje_personalizado = (
                    "El solicitante presenta un riesgo BAJO. "
                    "Puede acceder al monto completo del crédito sin restricciones especiales."
                )
                monto_recomendado = 15000


            return jsonify({
                "riesgo": riesgo,
                "probabilidad": round(probabilidad, 4),  # valor normal, sin multiplicar por 100

                # Datos del solicitante
                "nombre": nombre_solicitante,
                "dni": data.get("dni_solicitante"),
       
                # Mensajes mejorados
                "mensaje": mensaje_personalizado,
                "monto_recomendado": monto_recomendado

            })

        except Exception as e:
            import traceback
            print("Error en predicción:", e)
            traceback.print_exc()
            return jsonify({"error": "Error al procesar la predicción"}), 500

    return render_template(
        'prediccion.html', 
        rol=session.get('rol'), 
        active_page='prediccion'
    )






# VALIDADCION SOLICITANTE REGISTRADO
@prediccion_bp.route("/buscar_solicitante", methods=["GET"])
@login_requerido
@role_requerido(['administrador', 'analista'])
def buscar_solicitante():
    dni = request.args.get("dni")
    
    if not dni:
        return jsonify({"existe": False, "error": "No se proporcionó DNI"}), 400
    
    # Buscar el solicitante en la base de datos
    solicitante = Prediccion.query.filter_by(dni_solicitante=dni).first()
    
    if solicitante:
        return jsonify({
            "existe": True,
            "nombre_solicitante": solicitante.nombre_solicitante,
            "edad_solicitante": solicitante.Edad
        })
    else:
        return jsonify({"existe": False})






# ESTADISTICAS DEL DIA
@prediccion_bp.route('/estadisticas-dia', methods=['GET'])
@login_requerido
@role_requerido(['administrador', 'analista'])
def obtener_estadisticas_dia():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({"error": "Usuario no autenticado"}), 401

    try:
        hoy = datetime.today().date()
        predicciones_hoy = Prediccion.query.filter_by(usuario_id=usuario_id, fecha_prediccion=hoy).all()
        total = len(predicciones_hoy)

        if total == 0:
            return jsonify({
                "total_evaluaciones": 0,
                "riesgo_bajo": {"cantidad": 0, "promedio_probabilidad": 0},
                "riesgo_medio": {"cantidad": 0, "promedio_probabilidad": 0},
                "riesgo_alto": {"cantidad": 0, "promedio_probabilidad": 0}
            })

        # Inicializar contadores y sumas
        contador = {"BAJO": 0, "MEDIO": 0, "ALTO": 0}
        suma_prob = {"BAJO": 0.0, "MEDIO": 0.0, "ALTO": 0.0}

        for p in predicciones_hoy:
            nivel = p.nivel_riesgo.upper()
            if nivel in contador:
                contador[nivel] += 1
                suma_prob[nivel] += p.probabilidad_default

        # Calcular promedios
        promedio = {
            nivel: round(suma_prob[nivel]/contador[nivel], 4) if contador[nivel] > 0 else 0
            for nivel in contador
        }

        return jsonify({
            "total_evaluaciones": total,
            "riesgo_bajo": {"cantidad": contador["BAJO"], "promedio_probabilidad": promedio["BAJO"]},
            "riesgo_medio": {"cantidad": contador["MEDIO"], "promedio_probabilidad": promedio["MEDIO"]},
            "riesgo_alto": {"cantidad": contador["ALTO"], "promedio_probabilidad": promedio["ALTO"]}
        })

    except Exception as e:
        import traceback
        print("Error en estadisticas del día:", e)
        traceback.print_exc()
        return jsonify({"error": "Error al obtener estadísticas"}), 500






    

# ===============================
# IMPORTACIÓN DE CSV PARA AUTOCOMPLETAR FORMULARIO
# ===============================
@prediccion_bp.route('/cargar_csv', methods=['POST'])
def cargar_csv():
    file = request.files.get('file')
    if not file:
        return jsonify(success=False, message="No se envió un archivo"), 400

    try:
        df = pd.read_csv(file)

        # Normalizamos columnas del CSV
        csv_cols = {col.lower(): col for col in df.columns}

        # ====== MAPEO COMPLETO DE CAMPOS ======
        # Clave = nombre REAL del campo en el formulario
        # Lista = todas las variantes aceptadas en el CSV
        field_map = {
            "dni_solicitante": ["dni_solicitante", "dni", "documento", "nro_dni"],
            "nombre_solicitante": ["nombre_solicitante", "nombre", "nombres", "cliente"],
            "Edad": ["edad", "Edad", "anios", "años"],
            "Ocupacion": ["ocupacion", "profesion", "empleo"],
            "Ingreso_Anual": ["ingreso_anual", "ingresos_anuales", "annual_income"],
            "Salario_Mensual_Mano": ["salario_mensual", "salario", "salario_mano"],
            "Nro_Cuentas_Bancarias": ["nro_cuentas_bancarias", "cuentas_bancarias", "nro_cuentas"],
            "Nro_Tarjetas_Credito": ["nro_tarjetas_credito", "tarjetas_credito", "cantidad_tarjetas"],
            "Tasa_Interes": ["tasa_interes", "interes", "tasa"],
            "Nro_Prestamos": ["nro_prestamos", "prestamos", "cantidad_prestamos"],
            "Tipo_Prestamo": ["tipo_prestamo", "tipo_credito", "categoria_prestamo"],
            "Cambio_Limite_Credito": ["cambio_limite_credito", "limite_credito_cambio"],
            "Nro_Consultas_Credito": ["nro_consultas_credito", "consultas_credito"],
            "Deuda_Pendiente": ["deuda_pendiente", "deuda_total"],
            "Ratio_Utilizacion_Credito": ["ratio_utilizacion_credito", "utilizacion_credito"],
            "Antiguedad_Historial_Credito": ["antiguedad_historial_credito", "historial_antiguedad"],
            "EMI_Total_Mensual": ["emi_total_mensual", "emi_mensual"],
            "Monto_Invertido_Mensualmente": ["monto_invertido_mensualmente", "inversion_mensual"],
            "Puntaje_Credito": ["puntaje_credito", "score_credito", "credit_score"],
            "Ratio_Deuda_Ingreso": ["ratio_deuda_ingreso", "deuda_ingreso"],
            "Ratio_EMI_Ingreso": ["ratio_emi_ingreso", "emi_ingreso"],
            "Ahorro_Mensual": ["ahorro_mensual", "ahorros"],
            "Sector_Economico": ["sector_economico", "sector", "actividad_economica"],
            "Infocorp_Flag": ["infocorp_flag", "infocorp", "en_infocorp"],
            "Region": ["region", "departamento", "zona"]
        }

        # === Procesar fila 0 del CSV ===
        row_data = {}
        first_row = df.iloc[0]

        for form_field, posibles_nombres in field_map.items():
            valor = None

            # Buscar cada nombre posible dentro de las columnas del CSV
            for posible in posibles_nombres:
                if posible.lower() in csv_cols:
                    csv_name = csv_cols[posible.lower()]
                    valor = first_row[csv_name]
                    break

            if valor is not None:
                row_data[form_field] = str(valor)

        return jsonify(success=True, data=row_data)

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500










import traceback
# ============================================================== 
# PREDICCIÓN PARA EL USUARIO BÁSICO (MODO DEMO) 
# ============================================================== 
@prediccion_bp.route('/prediccion_basico', methods=['GET', 'POST'])
@login_requerido
@role_requerido(['usuario_basico'])
def prediccion_basico():
    usuario_id = session.get('usuario_id')
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario o JSON
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()

            # -----------------------------
            # CAMPOS NUMÉRICOS CON VALORES POR DEFECTO
            # -----------------------------
            campos_numericos = [
                'Edad', 'Ingreso_Anual', 'Salario_Mensual_Mano',
                'Nro_Cuentas_Bancarias', 'Nro_Tarjetas_Credito',
                'Deuda_Pendiente', 'Tipo_Prestamo',
                'Monto_Invertido_Mensualmente', 'Tasa_Interes', 'dependientes'
            ]
            for campo in campos_numericos:
                try:
                    data[campo] = float(data.get(campo, 0))
                except ValueError:
                    data[campo] = 0

            # -----------------------------
            # CAMPOS CATEGÓRICOS/INFORMATIVOS
            # -----------------------------
            genero_map = {"Masculino": 0, "Femenino": 1}
            casado_map = {"Sí": 1, "No": 0}
            educacion_map = {"Graduado": 0, "No Graduado": 1}
            zona_map = {"Rural": 0, "Semiurbana": 1, "Urbana": 2}

            # Asignar valores
            genero = genero_map.get(data.get('genero'), 0)
            casado = casado_map.get(data.get('casado'), 0)
            educacion = educacion_map.get(data.get('educacion'), 0)
            zona_propiedad = zona_map.get(data.get('zona_propiedad'), 0)
            dependientes = int(data.get('dependientes', 0))

            # -----------------------------
            # CREAR DATAFRAME PARA EL MODELO
            # -----------------------------
            df_modelo = pd.DataFrame([{
                "Edad": float(data.get("Edad", 0)),
                "Ingreso_Anual": float(data.get("Ingreso_Anual", 0)),
                "Salario_Mensual_Mano": float(data.get("Salario_Mensual_Mano", 0)),
                "Nro_Cuentas_Bancarias": int(data.get("Nro_Cuentas_Bancarias", 0)),
                "Nro_Tarjetas_Credito": int(data.get("Nro_Tarjetas_Credito", 0)),
                "Deuda_Pendiente": float(data.get("Deuda_Pendiente", 0)),
                "Tipo_Prestamo": int(data.get("Tipo_Prestamo", 0)),
                "Monto_Invertido_Mensualmente": float(data.get("Monto_Invertido_Mensualmente", 0)),
                "Tasa_Interes": float(data.get("Tasa_Interes", 0))
            }])

            # -----------------------------
            # PREDICCIÓN
            # -----------------------------
            prediccion = int(modelo_basico.predict(df_modelo)[0])
            probabilidad = float(modelo_basico.predict_proba(df_modelo)[0][1])

            if probabilidad < 0.33:
                nivel_riesgo = "Bajo"
            elif probabilidad < 0.66:
                nivel_riesgo = "Medio"
            else:
                nivel_riesgo = "Alto"

            # -----------------------------
            # GUARDAR EN BASE DE DATOS
            # -----------------------------
            nueva_prediccion = PrediccionBasico(
                usuario_id=usuario_id,
                nombre_solicitante=data.get('nombre_solicitante'),
                genero=data.get('genero'),
                casado=data.get('casado'),
                dependientes=dependientes,
                educacion=data.get('educacion'),
                zona_propiedad=data.get('zona_propiedad'),
                Edad=int(data.get('Edad', 0)),
                Ingreso_Anual=float(data.get('Ingreso_Anual', 0)),
                Salario_Mensual_Mano=float(data.get('Salario_Mensual_Mano', 0)),
                Nro_Cuentas_Bancarias=int(data.get('Nro_Cuentas_Bancarias', 0)),
                Nro_Tarjetas_Credito=int(data.get('Nro_Tarjetas_Credito', 0)),
                Deuda_Pendiente=float(data.get('Deuda_Pendiente', 0)),
                Tipo_Prestamo=int(data.get('Tipo_Prestamo', 0)),
                Monto_Invertido_Mensualmente=float(data.get('Monto_Invertido_Mensualmente', 0)),
                Tasa_Interes=float(data.get('Tasa_Interes', 0)),
                probabilidad_default=probabilidad,
                nivel_riesgo=nivel_riesgo,
                estado_prediccion="EXITO"
            )

            db.session.add(nueva_prediccion)
            db.session.commit()

            # -----------------------------
            # RETORNAR RESPUESTA CON DATOS PARA RECOMENDACIONES
            # -----------------------------
            return jsonify({
                "riesgo": nivel_riesgo,
                "probabilidad": round(probabilidad, 4),
                "mensaje": "Predicción realizada y guardada correctamente."
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    # -----------------------------
    # GET: PASAR ÚLTIMA PREDICCIÓN AL TEMPLATE
    # -----------------------------
    ultima_prediccion = PrediccionBasico.query.filter_by(usuario_id=usuario_id)\
                          .order_by(PrediccionBasico.id.desc()).first()

    return render_template(
        'prediccion_basico.html', 
        ultima_prediccion=ultima_prediccion,
        rol=session.get('rol', ''),
        pagina_actual='prediccion_basico',   # 🔥 NECESARIO
        active_page='prediccion_basico'
        )


