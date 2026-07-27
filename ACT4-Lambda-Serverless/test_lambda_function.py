
import json

from lambda_function import lambda_handler, NIVELES_VALIDOS


def _invoke(query_params=None):
    """Construye un evento minimo de Function URL y llama al handler."""
    event = {"queryStringParameters": query_params}
    response = lambda_handler(event, context=None)
    body = json.loads(response["body"])
    return response, body


def test_sin_parametro_devuelve_universal():
    response, body = _invoke(query_params=None)
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"
    assert body["nivel"] == "universal"
    assert set(body.keys()) == {"excusa", "nivel", "credibilidad", "tip"}


def test_query_params_vacio_devuelve_universal():
    response, body = _invoke(query_params={})
    assert body["nivel"] == "universal"


def test_nivel_junior():
    _, body = _invoke(query_params={"nivel": "junior"})
    assert body["nivel"] == "junior"


def test_nivel_mid():
    _, body = _invoke(query_params={"nivel": "mid"})
    assert body["nivel"] == "mid"


def test_nivel_senior():
    _, body = _invoke(query_params={"nivel": "senior"})
    assert body["nivel"] == "senior"


def test_nivel_invalido_cae_a_universal():
    _, body = _invoke(query_params={"nivel": "experto-supremo"})
    assert body["nivel"] == "universal"


def test_nivel_con_mayusculas_y_espacios():
    _, body = _invoke(query_params={"nivel": "  SENIOR  "})
    assert body["nivel"] == "senior"


def test_respuesta_es_json_valido_serializable():
    _, body = _invoke(query_params={"nivel": "junior"})
    assert isinstance(body, dict)


def test_multiples_llamadas_pueden_variar():
    excusas_obtenidas = set()
    for _ in range(20):
        _, body = _invoke(query_params={"nivel": "mid"})
        excusas_obtenidas.add(body["excusa"])
    assert len(excusas_obtenidas) >= 1 


if __name__ == "__main__":
    import sys
    import traceback

    tests = [
        test_sin_parametro_devuelve_universal,
        test_query_params_vacio_devuelve_universal,
        test_nivel_junior,
        test_nivel_mid,
        test_nivel_senior,
        test_nivel_invalido_cae_a_universal,
        test_nivel_con_mayusculas_y_espacios,
        test_respuesta_es_json_valido_serializable,
        test_multiples_llamadas_pueden_variar,
    ]

    failures = 0
    for test in tests:
        try:
            test()
            print(f"OK   - {test.__name__}")
        except AssertionError:
            failures += 1
            print(f"FAIL - {test.__name__}")
            traceback.print_exc()

    print(f"\n{len(tests) - failures}/{len(tests)} tests pasaron")
    sys.exit(1 if failures else 0)
