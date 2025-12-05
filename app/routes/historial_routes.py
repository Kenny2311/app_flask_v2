from flask import Blueprint, render_template, session, Response, request, make_response
from app.utils.autentication import login_requerido
from app.utils.autentication import role_requerido

from flask import jsonify
import csv
from datetime import datetime
from app import db
from sqlalchemy.orm import aliased
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import make_response
from io import BytesIO
import json

from app.models.prediccion_models import Prediccion
from app.models.prediccion_basico_models import PrediccionBasico

historial_bp = Blueprint('historial', __name__, template_folder='../templates')


# Función auxiliar para categorizar riesgo
def categorizar_riesgo(probabilidad):
    if probabilidad is None:
        return "-"
    if probabilidad <= 0.40:
        return "BAJO"
    elif probabilidad <= 0.70:
        return "MEDIO"
    else:
        return "ALTO"




  
# FILTRADO DE BUSQUEDA DE EVALUACIONES CREDITICIAS   
@historial_bp.route('/filtrar_evaluaciones_crediticias', methods=['GET', 'POST'])
@login_requerido
@role_requerido(['administrador', 'analista'])
def filtrar_evaluaciones_crediticias():
    rol_actual = session.get('rol')
    usuario_id = session.get('usuario_id')

    # Inicializamos el query
    historial_query = Prediccion.query

    # Filtrado según rol
    if rol_actual != 'administrador':
        historial_query = historial_query.filter_by(usuario_id=usuario_id)

    # --- FILTRADO POR FORMULARIO ---
    if request.method == 'POST':
        # Ejemplo de filtros desde un formulario
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        nivel_riesgo = request.form.get('nivel_riesgo')

        if fecha_inicio:
            historial_query = historial_query.filter(Prediccion.fecha >= fecha_inicio)
        if fecha_fin:
            historial_query = historial_query.filter(Prediccion.fecha <= fecha_fin)
        if nivel_riesgo and nivel_riesgo != 'Todos':
            historial_query = historial_query.filter(Prediccion.nivel_riesgo.ilike(nivel_riesgo))

    # Orden descendente por ID (más reciente primero)
    historial = historial_query.order_by(Prediccion.id.desc()).all()

    # --- RESUMEN DE ESTADÍSTICAS PARA SIDEBAR ---
    total_predicciones = len(historial)

    # Riesgo ALTO
    alto = [r for r in historial if r.nivel_riesgo and r.nivel_riesgo.upper() == 'ALTO']
    total_alto = len(alto)
    promedio_alto = sum(r.probabilidad_default for r in alto) / total_alto if total_alto else 0

    # Riesgo BAJO
    bajo = [r for r in historial if r.nivel_riesgo and r.nivel_riesgo.upper() == 'BAJO']
    total_bajo = len(bajo)
    promedio_bajo = sum(r.probabilidad_default for r in bajo) / total_bajo if total_bajo else 0

    # Riesgo MEDIO
    medio = [r for r in historial if r.nivel_riesgo and r.nivel_riesgo.upper() == 'MEDIO']
    total_medio = len(medio)
    promedio_medio = sum(r.probabilidad_default for r in medio) / total_medio if total_medio else 0

    return render_template(
        'filtrar_evaluaciones_crediticias.html',
        historial=historial,
        total_predicciones=total_predicciones,
        total_alto=total_alto,
        promedio_alto=promedio_alto,
        total_bajo=total_bajo,
        promedio_bajo=promedio_bajo,
        total_medio=total_medio,
        promedio_medio=promedio_medio,
        active_page='filtrar_evaluaciones_crediticias',
        rol=rol_actual
    )









# BUSCAR PREDICCIONES POR DNI
@historial_bp.route('/buscar_predicciones', methods=['GET'])
@login_requerido
def buscar_predicciones():
    dni = request.args.get('dni_solicitante', '').strip()  # Solo buscamos por DNI
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    nivel_riesgo = request.args.get('nivel_riesgo', '').upper()
    usuario_id = session.get('usuario_id')
    rol_actual = session.get('rol')

    query = Prediccion.query

    # Filtrar por rol (los no administradores solo ven sus predicciones)
    if rol_actual != 'administrador':
        query = query.filter_by(usuario_id=usuario_id)

    # Filtrar por DNI
    if dni:
        query = query.filter(Prediccion.dni_solicitante.ilike(f"%{dni}%"))

    # Filtrar por rango de fechas
    if fecha_desde:
        fecha_desde_dt = datetime.strptime(fecha_desde, "%Y-%m-%d")
        query = query.filter(Prediccion.fecha_prediccion >= fecha_desde_dt)
    if fecha_hasta:
        fecha_hasta_dt = datetime.strptime(fecha_hasta, "%Y-%m-%d")
        query = query.filter(Prediccion.fecha_prediccion <= fecha_hasta_dt)

    resultados = query.order_by(Prediccion.id.desc()).all()

    # Preparar datos para JSON
    data = []
    for pred in resultados:
        riesgo_categoria = categorizar_riesgo(pred.probabilidad_default)

        # Filtrar por riesgo si se especifica
        if nivel_riesgo and riesgo_categoria != nivel_riesgo:
            continue

        data.append({
            "id": pred.id,
            "dni_solicitante": pred.dni_solicitante,
            "nombre_solicitante": pred.nombre_solicitante,
            "fecha_prediccion": pred.fecha_prediccion.strftime("%d/%m/%Y") if pred.fecha_prediccion else "",
            "probabilidad": pred.probabilidad_default,
            "riesgo": riesgo_categoria
        })

    return jsonify(data)


# HISTORIAL PREDICCIONES COMPLETO
@historial_bp.route('/historial_predicciones', methods=['GET'])
@login_requerido
@role_requerido(['administrador', 'analista'])
def historial_predicciones():
    rol_actual = session.get('rol')
    usuario_id = session.get('usuario_id')

    # Predicciones según rol
    if rol_actual == 'administrador':
        historial = Prediccion.query.order_by(Prediccion.id.desc()).all()
    else:
        historial = Prediccion.query.filter_by(usuario_id=usuario_id).order_by(Prediccion.id.desc()).all()

    # --- RESUMEN PARA LA SIDEBAR ---
    total_predicciones = len(historial)

    # Riesgo ALTO
    alto = [r for r in historial if r.nivel_riesgo and r.nivel_riesgo.upper() == 'ALTO']
    total_alto = len(alto)
    promedio_alto = sum(r.probabilidad_default for r in alto) / total_alto if total_alto else 0

    # Riesgo BAJO
    bajo = [r for r in historial if r.nivel_riesgo and r.nivel_riesgo.upper() == 'BAJO']
    total_bajo = len(bajo)
    promedio_bajo = sum(r.probabilidad_default for r in bajo) / total_bajo if total_bajo else 0

    # Riesgo MEDIO
    medio = [r for r in historial if r.nivel_riesgo and r.nivel_riesgo.upper() == 'MEDIO']
    total_medio = len(medio)
    promedio_medio = sum(r.probabilidad_default for r in medio) / total_medio if total_medio else 0

    return render_template(
        'historial_predicciones.html',
        historial=historial,
        total_predicciones=total_predicciones,
        total_alto=total_alto,
        promedio_alto=promedio_alto,
        total_bajo=total_bajo,
        promedio_bajo=promedio_bajo,
        total_medio=total_medio,
        promedio_medio=promedio_medio,
        active_page='historial_predicciones',
        rol=session.get('rol')
    )

# BUSCAR EN HISTORIAL COMPLETO
@historial_bp.route('/buscar_predicciones_avanzado', methods=['GET'])
@login_requerido
@role_requerido(['administrador', 'analista'])
def buscar_predicciones_avanzado():
    rol_actual = session.get('rol')
    usuario_id = session.get('usuario_id')
    query = Prediccion.query

    if rol_actual != 'administrador':
        query = query.filter_by(usuario_id=usuario_id)

    # Aplicar filtros
    dni = request.args.get('dni_solicitante', '').strip()
    nombre = request.args.get('nombre_solicitante', '').strip()
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    nivel_riesgo = request.args.get('nivel_riesgo', '').upper()

    if dni:
        query = query.filter(Prediccion.dni_solicitante.ilike(f"%{dni}%"))
    if nombre:
        query = query.filter(Prediccion.nombre_solicitante.ilike(f"%{nombre}%"))
    if fecha_desde:
        fecha_desde_dt = datetime.strptime(fecha_desde, "%Y-%m-%d")
        query = query.filter(Prediccion.fecha_prediccion >= fecha_desde_dt)
    if fecha_hasta:
        fecha_hasta_dt = datetime.strptime(fecha_hasta, "%Y-%m-%d")
        query = query.filter(Prediccion.fecha_prediccion <= fecha_hasta_dt)

    resultados = query.order_by(Prediccion.id.desc()).all()

    data = []
    for p in resultados:
        riesgo_categoria = categorizar_riesgo(p.probabilidad_default)
        if nivel_riesgo and riesgo_categoria != nivel_riesgo:
            continue

        data.append({
            "dni_solicitante": p.dni_solicitante,
            "nombre_solicitante": p.nombre_solicitante,
            "fecha_prediccion": p.fecha_prediccion.strftime('%d/%m/%Y') if p.fecha_prediccion else "",
            "modelo_version": p.modelo_version,
            "estado_prediccion": p.estado_prediccion,
            "tiempo_inferencia_ms": p.tiempo_inferencia_ms,
            "probabilidad_default": p.probabilidad_default,
            "nivel_riesgo": riesgo_categoria,
            "Edad": p.Edad,
            "Ocupacion": p.Ocupacion,
            "Ingreso_Anual": p.Ingreso_Anual,
            "Salario_Mensual_Mano": p.Salario_Mensual_Mano,
            "Nro_Cuentas_Bancarias": p.Nro_Cuentas_Bancarias,
            "Nro_Tarjetas_Credito": p.Nro_Tarjetas_Credito,
            "Tasa_Interes": p.Tasa_Interes,
            "Nro_Prestamos": p.Nro_Prestamos,
            "Tipo_Prestamo": p.Tipo_Prestamo,
            "Cambio_Limite_Credito": p.Cambio_Limite_Credito,
            "Nro_Consultas_Credito": p.Nro_Consultas_Credito,
            "Deuda_Pendiente": p.Deuda_Pendiente,
            "Ratio_Utilizacion_Credito": p.Ratio_Utilizacion_Credito,
            "Antiguedad_Historial_Credito": p.Antiguedad_Historial_Credito,
            "EMI_Total_Mensual": p.EMI_Total_Mensual,
            "Monto_Invertido_Mensualmente": p.Monto_Invertido_Mensualmente,
            "Puntaje_Credito": p.Puntaje_Credito,
            "Ratio_Deuda_Ingreso": p.Ratio_Deuda_Ingreso,
            "Ratio_EMI_Ingreso": p.Ratio_EMI_Ingreso,
            "Ahorro_Mensual": p.Ahorro_Mensual,
            "Sector_Economico": p.Sector_Economico,
            "Infocorp_Flag": p.Infocorp_Flag,
            "Region": p.Region
        })

    return jsonify(data)





# DESCARGAR CSV COMPLETO
@historial_bp.route('/descargar_csv')
@login_requerido
@role_requerido(['administrador', 'analista', 'usuario_basico']) 
def descargar_csv():
    historial = Prediccion.query.all()

    if not historial:
        return "No hay datos para descargar", 404

    def generar_csv():
        encabezados = [
            'ID', 'USUARIO_ID', 'DNI', 'Nombre_Solicitante', 'Fecha_Prediccion',
            'Modelo_Version', 'Estado_Prediccion', 'Tiempo_Inferencia_ms',
            'Probabilidad_Default', 'Nivel_Riesgo', 'Variables_Importantes',
            'Edad', 'Ocupacion', 'Ingreso_Anual', 'Salario_Mensual_Mano',
            'Nro_Cuentas_Bancarias', 'Nro_Tarjetas_Credito', 'Tasa_Interes',
            'Nro_Prestamos', 'Tipo_Prestamo', 'Cambio_Limite_Credito',
            'Nro_Consultas_Credito', 'Deuda_Pendiente', 'Ratio_Utilizacion_Credito',
            'Antiguedad_Historial_Credito', 'EMI_Total_Mensual',
            'Monto_Invertido_Mensualmente', 'Puntaje_Credito', 'Ratio_Deuda_Ingreso',
            'Ratio_EMI_Ingreso', 'Ahorro_Mensual', 'Sector_Economico',
            'Infocorp_Flag', 'Region'
        ]

        yield ','.join(encabezados) + '\n'

        for p in historial:
            fila = [
                str(p.id), str(p.usuario_id), p.dni_solicitante, p.nombre_solicitante,
                p.fecha_prediccion.strftime("%d/%m/%Y") if p.fecha_prediccion else "",
                p.modelo_version or "", p.estado_prediccion or "", str(p.tiempo_inferencia_ms or ""),
                str(p.probabilidad_default or ""), p.nivel_riesgo or "", p.variables_importantes or "",
                str(p.Edad or ""), p.Ocupacion or "", str(p.Ingreso_Anual or ""), str(p.Salario_Mensual_Mano or ""),
                str(p.Nro_Cuentas_Bancarias or ""), str(p.Nro_Tarjetas_Credito or ""), str(p.Tasa_Interes or ""),
                str(p.Nro_Prestamos or ""), p.Tipo_Prestamo or "", str(p.Cambio_Limite_Credito or ""),
                str(p.Nro_Consultas_Credito or ""), str(p.Deuda_Pendiente or ""), str(p.Ratio_Utilizacion_Credito or ""),
                str(p.Antiguedad_Historial_Credito or ""), str(p.EMI_Total_Mensual or ""),
                str(p.Monto_Invertido_Mensualmente or ""), str(p.Puntaje_Credito or ""), str(p.Ratio_Deuda_Ingreso or ""),
                str(p.Ratio_EMI_Ingreso or ""), str(p.Ahorro_Mensual or ""), p.Sector_Economico or "",
                'Sí' if p.Infocorp_Flag == 1 else 'No', p.Region or ""
            ]
            yield ','.join(fila) + '\n'

    return Response(
        generar_csv(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=historial_predicciones.csv'
        }
    )




# VER REPORTE DE PREDICCION
@historial_bp.route('/ver_reporte/<int:id>', methods=['GET'])
@login_requerido
@role_requerido(['administrador', 'analista', 'usuario_basico'])
def ver_reporte(id):
    prediccion = Prediccion.query.get_or_404(id)

    riesgo_categoria = categorizar_riesgo(prediccion.probabilidad_default)

    # --- Convertir variables_importantes (JSON string) a dict ---
    import json
    try:
        variables_importantes = json.loads(prediccion.variables_importantes) \
            if prediccion.variables_importantes else {}
    except:
        variables_importantes = {}

    return render_template(
        'reporte_prediccion.html',
        prediccion=prediccion,
        riesgo_categoria=riesgo_categoria,
        variables_importantes=variables_importantes,   # <-- IMPORTANTE
        datetime=datetime
    )



# REPORTE COMPLETO DE PREDICCION EN PDF
@historial_bp.route("/reporte_prediccion_pdf/<int:id>", methods=["GET"])
@login_requerido
def reporte_prediccion_pdf(id):
    import json
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO

    pred = Prediccion.query.get_or_404(id)
    riesgo = categorizar_riesgo(pred.probabilidad_default)

    # Parsear variables importantes (si existen)
    try:
        variables_importantes = json.loads(pred.variables_importantes) if pred.variables_importantes else {}
    except:
        variables_importantes = {}

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    y = 750  # posición inicial

    # Título
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "Reporte Completo de Predicción")
    y -= 40

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Información del Solicitante")
    y -= 20

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"DNI: {pred.dni_solicitante}")
    y -= 20
    pdf.drawString(50, y, f"Nombre: {pred.nombre_solicitante}")
    y -= 20
    pdf.drawString(50, y, f"Edad: {pred.Edad}")
    y -= 20
    pdf.drawString(50, y, f"Ocupación: {pred.Ocupacion}")
    y -= 20
    pdf.drawString(50, y, f"Región: {pred.Region}")
    y -= 20
    pdf.drawString(50, y, f"Sector Económico: {pred.Sector_Economico}")
    y -= 20
    pdf.drawString(50, y, f"Infocorp: {'Activo' if pred.Infocorp_Flag else 'Inactivo'}")
    y -= 30

    # Metadatos
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Datos de la Predicción")
    y -= 20

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Fecha: {pred.fecha_prediccion.strftime('%d/%m/%Y')}")
    y -= 20
    pdf.drawString(50, y, f"Modelo Versión: {pred.modelo_version}")
    y -= 20
    pdf.drawString(50, y, f"Tiempo de Inferencia (ms): {pred.tiempo_inferencia_ms}")
    y -= 30

    # Resultado
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Resultado del Modelo")
    y -= 20

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Probabilidad de Default: {pred.probabilidad_default * 100:.2f}%")
    y -= 20
    pdf.drawString(50, y, f"Nivel de Riesgo: {riesgo}")
    y -= 30

    # Datos financieros
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Datos Financieros Clave")
    y -= 20

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Ingreso Anual: {pred.Ingreso_Anual}")
    y -= 20
    pdf.drawString(50, y, f"Salario Mensual: {pred.Salario_Mensual_Mano}")
    y -= 20
    pdf.drawString(50, y, f"Ahorro Mensual: {pred.Ahorro_Mensual}")
    y -= 20
    pdf.drawString(50, y, f"Préstamos Activos: {pred.Nro_Prestamos}")
    y -= 20
    pdf.drawString(50, y, f"Tipo de Préstamo: {pred.Tipo_Prestamo}")
    y -= 20
    pdf.drawString(50, y, f"Tasa de Interés: {pred.Tasa_Interes}%")
    y -= 20
    pdf.drawString(50, y, f"Deuda Pendiente: {pred.Deuda_Pendiente}")
    y -= 30

    # Variables importantes del modelo
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Variables Más Influyentes")
    y -= 20
    pdf.setFont("Helvetica", 12)

    if variables_importantes:
        for key, val in variables_importantes.items():
            pdf.drawString(50, y, f"- {key}: {val}")
            y -= 18
            if y < 80:  
                pdf.showPage()
                y = 750
                pdf.setFont("Helvetica", 12)
    else:
        pdf.drawString(50, y, "No se registraron variables importantes.")
        y -= 20

    pdf.showPage()
    pdf.save()

    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=reporte_prediccion.pdf"
    return response










# ===============================================================
# HISTORIAL BÁSICO DE PREDICCIONES
# ===============================================================
@historial_bp.route('/historial_basico', methods=['GET'])
@login_requerido
@role_requerido(['usuario_basico'])
def historial_basico():
    rol_actual = session.get('rol')
    usuario_id = session.get('usuario_id')

    # Filtrar predicciones según el rol
    if rol_actual == 'administrador':
        historial = PrediccionBasico.query.order_by(PrediccionBasico.id.desc()).all()
    else:
        historial = PrediccionBasico.query.filter_by(usuario_id=usuario_id)\
                                          .order_by(PrediccionBasico.id.desc()).all()

    # Calcular totales de riesgo
    alto = [r for r in historial if r.nivel_riesgo and r.nivel_riesgo.upper() == 'ALTO']
    medio = [r for r in historial if r.nivel_riesgo and r.nivel_riesgo.upper() == 'MEDIO']
    bajo = [r for r in historial if r.nivel_riesgo and r.nivel_riesgo.upper() == 'BAJO']

    total_alto = len(alto)
    total_medio = len(medio)
    total_bajo = len(bajo)

    promedio_alto = sum(r.probabilidad_default for r in alto)/total_alto if total_alto else 0
    promedio_medio = sum(r.probabilidad_default for r in medio)/total_medio if total_medio else 0
    promedio_bajo = sum(r.probabilidad_default for r in bajo)/total_bajo if total_bajo else 0

    return render_template(
        'historial_basico.html',
        historial=historial,
        total_alto=total_alto,
        promedio_alto=promedio_alto,
        total_medio=total_medio,
        promedio_medio=promedio_medio,
        total_bajo=total_bajo,
        promedio_bajo=promedio_bajo,
        rol=session.get('rol', ''),
        pagina_actual='historial_basico',   # 🔥 NECESARIO
        active_page='historial_basico' 
    )


# DESCARGAR CSV DEL USUARIO BÁSICO
@historial_bp.route('/descargar_csv_basico')
@login_requerido
@role_requerido(['usuario_basico'])
def descargar_csv_basico():
    usuario_id = session.get('usuario_id')
    historial = PrediccionBasico.query.filter_by(usuario_id=usuario_id).all()

    if not historial:
        return "No hay datos para descargar", 404

    def generar_csv():
        encabezados = [
            'ID', 'Usuario_ID', 'Nombre_Solicitante', 'Fecha_Prediccion',
            'Genero', 'Casado', 'Dependientes', 'Educacion', 'Zona_Propiedad',
            'Edad', 'Ingreso_Anual', 'Salario_Mensual_Mano', 'Nro_Cuentas_Bancarias',
            'Nro_Tarjetas_Credito', 'Deuda_Pendiente', 'Tipo_Prestamo',
            'Monto_Invertido_Mensualmente', 'Tasa_Interes', 'Probabilidad_Default',
            'Nivel_Riesgo', 'Estado_Prediccion'
        ]
        yield ','.join(encabezados) + '\n'

        for p in historial:
            fila = [
                str(p.id), str(p.usuario_id), p.nombre_solicitante or "",
                p.fecha_prediccion.strftime("%d/%m/%Y") if p.fecha_prediccion else "",
                p.genero or "", p.casado or "", str(p.dependientes or ""), p.educacion or "", p.zona_propiedad or "",
                str(p.Edad or ""), str(p.Ingreso_Anual or ""), str(p.Salario_Mensual_Mano or ""),
                str(p.Nro_Cuentas_Bancarias or ""), str(p.Nro_Tarjetas_Credito or ""), str(p.Deuda_Pendiente or ""),
                str(p.Tipo_Prestamo or ""), str(p.Monto_Invertido_Mensualmente or ""), str(p.Tasa_Interes or ""),
                str(p.probabilidad_default or ""), p.nivel_riesgo or "", p.estado_prediccion or ""
            ]
            yield ','.join(fila) + '\n'

    return Response(
        generar_csv(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=historial_predicciones_basico.csv'
        }
    )