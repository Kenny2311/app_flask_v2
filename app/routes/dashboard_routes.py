from flask import Blueprint, render_template, session
from app.utils.autentication import login_requerido
from app.utils.autentication import role_requerido
from sqlalchemy import func
from datetime import datetime
from app.models.prediccion_models import Prediccion

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates')


def categorizar_riesgo(probabilidad):
    """Devuelve la categoría de riesgo según la probabilidad default."""
    if probabilidad is None:
        return "N/A"
    if probabilidad >= 0.7:
        return "ALTO"
    elif probabilidad >= 0.4:
        return "MEDIO"
    else:
        return "BAJO"


# Ruta principal del dashboard
@dashboard_bp.route('/dashboard')
@login_requerido
@role_requerido(['administrador', 'analista'])
def dashboard():
    rol_actual = session.get('rol')
    usuario_id = session.get('usuario_id')

    # Base query según el rol
    if rol_actual.lower() == 'administrador':
        query_base = Prediccion.query
    else:  # analista
        query_base = Prediccion.query.filter_by(usuario_id=usuario_id)

    # Total de predicciones
    total_predicciones = query_base.count()

    # Predicciones del mes actual
    mes_actual = datetime.utcnow().month
    predicciones_mes = query_base.filter(
        func.extract('month', Prediccion.fecha_prediccion) == mes_actual
    ).count()



    # Obtener todas las probabilidades
    resultados = query_base.with_entities(Prediccion.probabilidad_default).all()
    probabilidades = [r for r, in resultados if r is not None]

    # Contar por categoría
    total_bajo = sum(1 for r in probabilidades if categorizar_riesgo(r) == 'BAJO')
    total_medio = sum(1 for r in probabilidades if categorizar_riesgo(r) == 'MEDIO')
    total_alto = sum(1 for r in probabilidades if categorizar_riesgo(r) == 'ALTO')

    # Promedio real
    promedio_riesgo = round(sum(probabilidades)/len(probabilidades)*100, 2) if probabilidades else 0

    # Riesgo predominante
    if total_alto >= total_medio and total_alto >= total_bajo:
        riesgo_mas_alto = 'ALTO'
    elif total_medio >= total_bajo:
        riesgo_mas_alto = 'MEDIO'
    else:
        riesgo_mas_alto = 'BAJO'

    # Para las alertas
    if len(probabilidades) > 0:
        if total_alto / len(probabilidades) > 0.5:
            alerta_titulo = "⚠️ Alerta de Riesgo Alto"
            alerta_mensaje = f"El {round((total_alto / len(probabilidades)) * 100, 1)}% de las predicciones son de riesgo alto."
            alerta_color = "#fee2e2"
        elif total_medio / len(probabilidades) > 0.4:
            alerta_titulo = "⚠️ Riesgo Medio en Aumento"
            alerta_mensaje = f"El {round((total_medio / len(probabilidades)) * 100, 1)}% de las predicciones están en riesgo medio."
            alerta_color = "#fef3c7"
        elif total_bajo / len(probabilidades) > 0.7:
            alerta_titulo = "✅ Estabilidad Crediticia"
            alerta_mensaje = f"El {round((total_bajo / len(probabilidades)) * 100, 1)}% de los clientes presenta riesgo bajo."
            alerta_color = "#dcfce7"
        else:
            alerta_titulo = "ℹ️ Situación Neutral"
            alerta_mensaje = "Los niveles de riesgo se mantienen equilibrados."
            alerta_color = "#f3f4f6"
    else:
        alerta_titulo = "ℹ️ Sin datos de riesgo"
        alerta_mensaje = "No hay predicciones registradas."
        alerta_color = "#f3f4f6"



    # Última predicción realizada
    ultima_prediccion_obj = query_base.order_by(Prediccion.fecha_prediccion.desc()).first()
    ultima_prediccion = ultima_prediccion_obj.fecha_prediccion if ultima_prediccion_obj else None

    # Datos para gráfico de tendencia mensual
    meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    predicciones_por_mes = [
        query_base.filter(func.extract('month', Prediccion.fecha_prediccion) == i).count()
        for i in range(1, 13)
    ]

    # Distribución por sector económico
    sectores = []
    predicciones_por_sector = []
    resultados_sector = (
        query_base
        .with_entities(Prediccion.Sector_Economico, func.count(Prediccion.id))
        .group_by(Prediccion.Sector_Economico)
        .all()
    )
    for sector, cantidad in resultados_sector:
        sectores.append(sector if sector else "No especificado")
        predicciones_por_sector.append(cantidad)

    # Distribución de clientes por formalidad
    formales = query_base.filter(func.lower(Prediccion.Sector_Economico) == 'formal').count()
    informales = query_base.filter(func.lower(Prediccion.Sector_Economico) == 'informal').count()
    clientes_formal_informal = [formales, informales]

    # Distribución por región
    regiones = []
    predicciones_por_region = []
    resultados_region = (
        query_base
        .with_entities(Prediccion.Region, func.count(Prediccion.id))
        .group_by(Prediccion.Region)
        .all()
    )
    for region, cantidad in resultados_region:
        regiones.append(region if region else "No especificado")
        predicciones_por_region.append(cantidad)

    # Generar alerta según distribución de riesgo
    if len(probabilidades) > 0:
        if total_alto / len(probabilidades) > 0.5:
            alerta_titulo = "⚠️ Alerta de Riesgo Alto"
            alerta_mensaje = (
                f"El {round((total_alto / len(probabilidades)) * 100, 1)}% de las predicciones "
                "son de riesgo alto. Revisa las solicitudes recientes y valida ingresos o estabilidad laboral."
            )
            alerta_color = "#fee2e2"  # rojo claro
        elif total_medio / len(probabilidades) > 0.4:
            alerta_titulo = "⚠️ Riesgo Medio en Aumento"
            alerta_mensaje = (
                f"El {round((total_medio / len(probabilidades)) * 100, 1)}% de las predicciones "
                "se encuentran en riesgo medio. Ajusta los criterios de evaluación crediticia."
            )
            alerta_color = "#fef3c7"  # amarillo claro
        elif total_bajo / len(probabilidades) > 0.7:
            alerta_titulo = "✅ Estabilidad Crediticia"
            alerta_mensaje = (
                f"El {round((total_bajo / len(probabilidades)) * 100, 1)}% de los clientes presenta riesgo bajo. "
                "La cartera de crédito muestra un comportamiento saludable."
            )
            alerta_color = "#dcfce7"  # verde claro
        else:
            alerta_titulo = "ℹ️ Situación Neutral"
            alerta_mensaje = "Los niveles de riesgo se mantienen equilibrados, sin variaciones significativas."
            alerta_color = "#f3f4f6"  # gris claro
    else:
        alerta_titulo = "ℹ️ Sin datos de riesgo"
        alerta_mensaje = "No hay predicciones registradas para calcular alertas."
        alerta_color = "#f3f4f6"  # gris claro

    # Renderizar dashboard
    return render_template(
        'dashboard.html',
        total_predicciones=total_predicciones,
        predicciones_mes=predicciones_mes,
        promedio_riesgo=promedio_riesgo,
        ultima_prediccion=ultima_prediccion,
        total_bajo=total_bajo,
        total_medio=total_medio,
        total_alto=total_alto,
        meses=meses,
        predicciones_por_mes=predicciones_por_mes,
        sectores=sectores,
        predicciones_por_sector=predicciones_por_sector,
        regiones=regiones,
        predicciones_por_region=predicciones_por_region,
        clientes_formal_informal=clientes_formal_informal,
        alerta_titulo=alerta_titulo,
        alerta_mensaje=alerta_mensaje,
        alerta_color=alerta_color,
        rol=rol_actual,
        active_page='dashboard'
    )
