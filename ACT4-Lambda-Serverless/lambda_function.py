
import json
import random

# excusas por nivel junior mid y senior
EXCUSAS = {
    "junior": [
        {
            "excusa": "Estuve configurando mi ambiente de desarrollo",
            "credibilidad": "alta",
            "tip": "Funciona las primeras 3 veces",
        },
        {
            "excusa": "Mi npm install se quedo pegado toda la tarde",
            "credibilidad": "alta",
            "tip": "Nadie duda de npm, es sagrado",
        },
        {
            "excusa": "Estaba siguiendo un tutorial para entender el codigo legacy",
            "credibilidad": "media",
            "tip": "No menciones que era de YouTube",
        },
    ],
    "mid": [
        {
            "excusa": "Estuve refactorizando un modulo que nadie pidio pero lo necesitaba",
            "credibilidad": "media",
            "tip": "Ten a mano el nombre del modulo por si preguntan",
        },
        {
            "excusa": "Bloqueado esperando un review de PR que nadie aprobo",
            "credibilidad": "alta",
            "tip": "Clasico, y ademas es parcialmente cierto",
        },
        {
            "excusa": "Estuve depurando un bug intermitente que solo pasa en produccion",
            "credibilidad": "alta",
            "tip": "Nadie puede reproducirlo, nadie puede desmentirlo",
        },
    ],
    "senior": [
        {
            "excusa": "Estuve investigando una solucion de arquitectura para reducir la deuda tecnica",
            "credibilidad": "media",
            "tip": "Preparate para preguntas de seguimiento",
        },
        {
            "excusa": "Estuve evaluando el trade-off de migrar a un nuevo patron de diseno",
            "credibilidad": "media",
            "tip": "Ten un diagrama listo, por si acaso",
        },
        {
            "excusa": "Estuve en reuniones de alineamiento tecnico con otros equipos",
            "credibilidad": "alta",
            "tip": "Nadie te va a pedir el calendario",
        },
    ],
    # excusa cuando no se le pase el parametro nivel o no llega por algun motivo
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
    """
    Punto de entrada de la Lambda.

    Lee el query string param `nivel` desde el evento de la Function URL,
    selecciona una excusa aleatoria acorde al nivel (o universal si no se
    especifica o no es valido) y devuelve la respuesta HTTP en el formato
    esperado por Lambda func urls
    """
    # lee el parametro nivel si es que existe y lo guarda en la variable nivel
    query_params = event.get("queryStringParameters") or {}
    nivel = query_params.get("nivel")

    # se normaliza el nivel haciendo un .lower
    if nivel is not None:
        nivel = nivel.strip().lower()

    if nivel in NIVELES_VALIDOS:
        nivel_respuesta = nivel

    # y si no viene se usa el universal
    else:
        nivel_respuesta = "universal"


    # excusa aleatoria correspondiente al nivel usando un randomchoice
    excusa_elegida = random.choice(EXCUSAS[nivel_respuesta])

    # se arma el body de la respuesta con excusa el nivel la credibilidad y el tip
    body = {
        "excusa": excusa_elegida["excusa"],
        "nivel": nivel_respuesta,
        "credibilidad": excusa_elegida["credibilidad"],
        "tip": excusa_elegida["tip"],
    }

    # devolver respuesta
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }
