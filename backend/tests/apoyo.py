"""Utilidades compartidas por las pruebas."""

from sqlalchemy.orm import Session

CLAVE_ADMIN = "ClaveAdmin123!"
CLAVE_PROFESIONAL = "ClaveProf123!"


def override_db(conexion):
    """Sustituye get_db para que la API use la transaccion de la prueba."""

    def _get_db():
        sesion = Session(bind=conexion, join_transaction_mode="create_savepoint")
        try:
            yield sesion
        finally:
            sesion.close()

    return _get_db


def login(cliente, rut: str, password: str):
    return cliente.post(
        "/api/v1/auth/login",
        json={"rut": rut, "password": password},
    )


def token_de(cliente, rut: str, password: str) -> str:
    respuesta = login(cliente, rut, password)
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


def cabecera(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
