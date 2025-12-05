import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / '.env')

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise Exception("No se encontró OPENAI_API_KEY en las variables de entorno.")

client = OpenAI(api_key=api_key)

def obtener_respuesta_gpt(user_input, ventana, nombre_usuario='Usuario'):
    try:
        prompt_sistema = f"""
Eres un asistente integrado en un sistema Fintech. 
El usuario se encuentra actualmente en la ventana: {ventana}.
Su nombre de usuario es: {nombre_usuario}.
Tu tarea es responder de manera breve, clara y útil.
"""

        response = client.responses.create(
            model="gpt-5.1-mini",   # Puedes cambiar a gpt-5.1 o gpt-4o
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": user_input}
            ],
            max_output_tokens=150
        )

        return response.output_text

    except Exception as e:
        print("[ERROR GPT]", str(e))
        return "Ocurrió un error al contactar con el asistente."