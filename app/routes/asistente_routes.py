from flask import Blueprint, request, jsonify, session
from app.utils.autentication import login_requerido, role_requerido

asistente_bp = Blueprint('asistente', __name__, url_prefix='/asistente')

@asistente_bp.route('/asistente', methods=['POST'])
@login_requerido
@role_requerido(['usuario_basico'])
def asistente():
    data = request.get_json()
    user_text = data.get("message", "").strip().lower()
    ventana = data.get("ventana", "")
    nombre_usuario = session.get("nombre_completo", session.get("usuario", "Usuario"))

    # ---------------- Ventanas y respuestas ----------------
    respuestas_menu = {
        "hola": (
            f"👋 ¡Hola {nombre_usuario}! Bienvenid@ al menú principal.\n"
            "Elige una opción escribiendo el número o el nombre:\n"
            "1️⃣ Realizar predicción\n"
            "2️⃣ Ver historial\n"
            "3️⃣ Gestionar perfil\n"
            "Escribe 'ayuda' si necesitas orientación."
        ),
        "1": "🔮 Realizar predicción: completa el formulario y presiona 'Evaluarme'.",
        "realizar prediccion": "🔮 Realizar predicción: completa los datos y presiona 'Evaluarme'.",
        "2": "📂 Ver historial: consulta tus predicciones anteriores y detalles.",
        "ver historial": "📂 Ver historial: revisa tus evaluaciones y fechas.",
        "3": "⚙ Gestionar perfil: actualiza tu información o cambia tu contraseña.",
        "gestionar perfil": "⚙ Gestionar perfil: modifica tus datos y preferencias.",
        "ayuda": (
            "💡 Menú rápido:\n"
            "1️⃣ Realizar predicción → Ingresa datos y presiona 'Evaluarme'.\n"
            "2️⃣ Ver historial → Consulta tus evaluaciones anteriores.\n"
            "3️⃣ Gestionar perfil → Cambia tus datos o contraseña.\n"
            "✍️ Para salir, escribe 'adios'."
        ),
        "adios": "👋 ¡Hasta luego!"
    }

    respuestas_prediccion = {
    "inicio": f"🔮 {nombre_usuario}, estás en Predicción Básica.\n"
              "Ingresa tus datos en el formulario y presiona 'Evaluarme'.\n"
              "Si necesitas ayuda sobre un campo específico, escribe 'ayuda'.",
    "ayuda": (
        "💡 Puedes pedirme ayuda sobre cualquiera de estos campos escribiendo su número o nombre:\n"
        "1️⃣ Fecha de predicción\n"
        "2️⃣ Nombre del solicitante\n"
        "3️⃣ Edad\n"
        "4️⃣ Género\n"
        "5️⃣ Estado civil\n"
        "6️⃣ Personas a cargo\n"
        "7️⃣ Nivel de estudios\n"
        "8️⃣ Zona de propiedad\n"
        "9️⃣ Ingreso mensual fijo\n"
        "🔟 Ingreso anual estimado\n"
        "1️⃣1️⃣ Cuentas bancarias\n"
        "1️⃣2️⃣ Tarjetas de crédito\n"
        "1️⃣3️⃣ Monto de deuda actual\n"
        "1️⃣4️⃣ Tipo de préstamo más reciente\n"
        "1️⃣5️⃣ Monto invertido mensualmente\n"
        "1️⃣6️⃣ Tasa de interés promedio de tus créditos\n\n"
        "Escribe el número o nombre del campo para recibir indicaciones específicas."
    ),
    "1": "📅 Fecha de predicción: Ingresa la fecha actual en formato DD/MM/AAAA.",
    "fecha de predicción": "📅 Fecha de predicción: Ingresa la fecha actual en formato DD/MM/AAAA.",
    "2": "📝 Nombre del solicitante: Escribe el nombre completo del solicitante.",
    "nombre del solicitante": "📝 Nombre del solicitante: Escribe el nombre completo del solicitante.",
    "3": "🔢 Edad: Indica la edad del solicitante en años completos.",
    "edad": "🔢 Edad: Indica la edad del solicitante en años completos.",
    "4": "⚧ Género: Selecciona 'Masculino' o 'Femenino'.",
    "género": "⚧ Género: Selecciona 'Masculino' o 'Femenino'.",
    "5": "💍 Estado civil: Selecciona si está casado o soltero.",
    "estado civil": "💍 Estado civil: Selecciona si está casado o soltero.",
    # ... seguir para todos los campos ...
    "evaluarme": "🔮 Generando tu predicción... Por favor espera un momento.",
    "limpiar": "🧹 Se han limpiado todos los campos del formulario. Puedes volver a ingresar tus datos.",
    "adios": "👋 Hasta luego. Vuelve cuando quieras realizar otra predicción."
    }

    respuestas_historial = {
        "hola": f"📂 {nombre_usuario}, este es tu historial de predicciones. Puedes ver tus evaluaciones recientes y su nivel de riesgo.",
        "limpiar": "🧹 Los registros del historial han sido limpiados correctamente.",
        "detalle": (
            "🔍 Cada predicción muestra:\n"
            "• Fecha de predicción\n"
            "• Nombre del solicitante\n"
            "• Edad y género\n"
            "• Nivel de estudios y zona de propiedad\n"
            "• Ingresos, cuentas y tarjetas\n"
            "• Deuda, tipo de préstamo, inversión mensual\n"
            "• Tasa de interés, probabilidad de default y nivel de riesgo\n"
            "Puedes hacer clic en cada registro para ver estos detalles."
        ),
        "resumen": (
            "📊 Resumen de tus predicciones:\n"
            "• Alto riesgo: {total_alto} (promedio {promedio_alto:.2f}%)\n"
            "• Medio riesgo: {total_medio} (promedio {promedio_medio:.2f}%)\n"
            "• Bajo riesgo: {total_bajo} (promedio {promedio_bajo:.2f}%)\n"
            "Este resumen te ayuda a ver la tendencia general de tus evaluaciones."
        ),
        "ayuda": (
            "💡 Puedes usar los siguientes comandos:\n"
            "• 'detalle' → Para ver los datos de cada predicción.\n"
            "• 'resumen' → Para ver totales y promedios por nivel de riesgo.\n"
            "• 'limpiar' → Para eliminar todos tus registros.\n"
            "• 'adios' → Para cerrar la conversación."
        ),
        "adios": "👋 Hasta luego. Revisa tu historial cuando lo necesites."
    }

    # ---------------- Seleccionar diccionario según la ventana ----------------
    if ventana == "menu":
        respuestas_ventana = respuestas_menu
        mensaje_default = "❓ No entiendo tu mensaje. Escribe 'hola' o 'ayuda' para ver las opciones del menú."
    elif ventana == "prediccion_basico":
        respuestas_ventana = respuestas_prediccion
        mensaje_default = "❓ No entiendo tu mensaje. Escribe 'ayuda' para recibir instrucciones sobre la predicción."
    elif ventana == "historial_basico":
        respuestas_ventana = respuestas_historial
        mensaje_default = "❓ No entiendo tu mensaje. Escribe 'ayuda' para ver cómo interactuar con tu historial."
    else:
        respuestas_ventana = {}
        mensaje_default = "❓ No estoy seguro de dónde estás. Escribe 'ayuda' para recibir orientación."

    # ---------------- Buscar coincidencia parcial ----------------
    respuesta = mensaje_default
    for key, val in respuestas_ventana.items():
        if key in user_text:
            respuesta = val
            break
        # También considerar coincidencia aproximada para casos como 'predicción', 'historial', etc.
        elif any(word in user_text for word in key.split()):
            respuesta = val
            break

    return jsonify({"reply": respuesta})
