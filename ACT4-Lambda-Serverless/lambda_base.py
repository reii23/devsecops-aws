"""
Generador de Excusas para el Daily - Plantilla base
====================================================

Completa los TODO para implementar la Lambda. Cuando termines, el
comportamiento debe coincidir con lambda_function.py (la version resuelta
de este mismo reto).
"""

import json
import random

# Banco de excusas por nivel. Puedes agregar mas excusas a cada lista.
EXCUSAS = {
    "junior": [
        {
            "excusa": "Estuve configurando mi ambiente de desarrollo",
            "credibilidad": "alta",
            "tip": "Funciona las primeras 3 veces",
        },
    ],
    "mid": [
        {
            "excusa": "Bloqueado esperando un review de PR que nadie aprobo",
            "credibilidad": "alta",
            "tip": "Clasico, y ademas es parcialmente cierto",
        },
    ],
    "senior": [
        {
            "excusa": "Estuve investigando una solucion de arquitectura para reducir la deuda tecnica",
            "credibilidad": "media",
            "tip": "Preparate para preguntas de seguimiento",
        },
    ],
    "universal": [
        {
            "excusa": "Tuve problemas con Git",
            "credibilidad": "alta",
            "tip": "Clasico. Nunca falla.",
        },
    ],
}

NIVELES_VALIDOS = ("junior", "mid", "senior")


def lambda_handler(event, context):
    # TODO 1: Leer el query string param `nivel` desde el evento.
    #   Pista: event.get("queryStringParameters") puede ser None si no
    #   se envio ningun parametro, y es un dict si se enviaron parametros.
    #   El valor viene en la clave "nivel".
    nivel = None  # <-- reemplaza esto

    # TODO 2: Si `nivel` no es None, normalizalo (quita espacios, minusculas).

    # TODO 3: Decide el nivel final a usar:
    #   - Si `nivel` esta en NIVELES_VALIDOS, usa ese valor.
    #   - Si no (None, vacio, o un valor no reconocido), usa "universal".
    nivel_respuesta = "universal"  # <-- ajusta la logica

    # TODO 4: Elige una excusa aleatoria de EXCUSAS[nivel_respuesta]
    #   Pista: random.choice(lista)
    excusa_elegida = None  # <-- reemplaza esto

    # TODO 5: Construye el diccionario de respuesta con las claves:
    #   "excusa", "nivel", "credibilidad", "tip"
    body = {}  # <-- reemplaza esto

    # TODO 6: Devuelve la respuesta en el formato que espera
    #   Lambda Function URLs: statusCode, headers y body (string JSON).
    #   Pista: json.dumps(body)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": "{}",  # <-- reemplaza esto
    }
