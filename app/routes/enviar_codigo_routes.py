from flask import Blueprint, request, jsonify
import smtplib
from email.mime.text import MIMEText
import random

enviar_codigo_bp = Blueprint('enviar_codigo', __name__)

SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587
SMTP_USERNAME = "7faf29002@smtp-brevo.com"
SMTP_PASSWORD = "ZQwGCptDxARY3Evb"
EMAIL_FROM = "kenny.ayme.cuba@gmail.com"

@enviar_codigo_bp.route('/enviar-codigo', methods=['POST'])
def enviar_codigo():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"success": False, "message": "No se recibió el email"}), 400

    # Generar código aleatorio de 6 dígitos
    codigo = str(random.randint(100000, 999999))

    try:
        # Enviar correo
        msg = MIMEText(f"Tu código de verificación es: {codigo}")
        msg["Subject"] = "Código de verificación"
        msg["From"] = EMAIL_FROM
        msg["To"] = email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, [email], msg.as_string())

        return jsonify({"success": True, "message": "Código enviado correctamente"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
