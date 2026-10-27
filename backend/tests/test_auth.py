"""Pruebas de autenticacion, tokens y autorizacion por rol (Etapa 3)."""

import json

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import requiere_roles
from app.core.config import settings
from app.core.errors import registrar_manejadores
from app.core.security import (
    crear_token_acceso,
    hashear_password,
    verificar_password,
)
from app.db.session import get_db
from app.main import app as aplicacion
from app.models import RolUsuario, Usuario

CLAVE_ADMIN = "ClaveAdmin123!"
CLAVE_PROFESIONAL = "ClaveProf123!"


def _override_db(conexion):
    def _get_db():
        sesion = Session(bind=conexion, join_transaction_mode="create_savepoint")
        try:
            yield sesion
        finally:
            sesion.close()

    return _get_db


@pytest.fixture()
def usuarios_auth(datos_base):
    datos_base.execute(
        text("UPDATE usuarios SET password_hash = :h WHERE rut = :r"),
        {"h": hashear_password(CLAVE_ADMIN), "r": "11111111-1"},
    )
    datos_base.execute(
        text("UPDATE usuarios SET password_hash = :h WHERE rut = :r"),
        {"h": hashear_password(CLAVE_PROFESIONAL), "r": "22222222-2"},
    )
    datos_base.execute(
        text(
            """
            INSERT INTO usuarios
                (rut, nombres, apellidos, correo_electronico,
                 password_hash, rol, activo)
            VALUES
                ('66666666-6', 'Ines', 'Inactiva', 'ines@ejemplo.test',
                 :h, 'profesional', false)
            """
        ),
        {"h": hashear_password(CLAVE_PROFESIONAL)},
    )
    return datos_base


@pytest.fixture()
def cliente(usuarios_auth, conexion):
    aplicacion.dependency_overrides[get_db] = _override_db(conexion)
    try:
        with TestClient(aplicacion) as cliente_http:
            yield cliente_http
    finally:
        aplicacion.dependency_overrides.clear()


def login(cliente, rut: str, password: str):
    return cliente.post(
        "/api/v1/auth/login",
        json={"rut": rut, "password": password},
    )


def token_de(cliente, rut: str, password: str) -> str:
    respuesta = login(cliente, rut, password)
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


def test_login_correcto_de_administrador(cliente):
    respuesta = login(cliente, "11111111-1", CLAVE_ADMIN)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["expires_in"] == settings.access_token_expire_minutes * 60
    assert cuerpo["usuario"] == {
        "rut": "11111111-1",
        "nombres": "Ana",
        "apellidos": "Administradora",
        "rol": "administrador",
    }
    assert "password" not in json.dumps(cuerpo).lower()


def test_login_normaliza_el_rut(cliente):
    respuesta = login(cliente, "11.111.111-1", CLAVE_ADMIN)
    assert respuesta.status_code == 200
    assert respuesta.json()["usuario"]["rut"] == "11111111-1"


def test_login_con_password_incorrecta(cliente):
    respuesta = login(cliente, "11111111-1", "clave-equivocada")
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["codigo"] == "credenciales_invalidas"


def test_login_rut_inexistente_no_revela_la_existencia(cliente):
    incorrecta = login(cliente, "11111111-1", "clave-equivocada")
    inexistente = login(cliente, "12345678-9", CLAVE_ADMIN)

    assert inexistente.status_code == 401
    assert (
        inexistente.json()["error"]["mensaje"]
        == incorrecta.json()["error"]["mensaje"]
    )


def test_login_con_rut_invalido(cliente):
    respuesta = login(cliente, "12.345.678-9", CLAVE_ADMIN)
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["codigo"] == "credenciales_invalidas"


def test_login_de_cuenta_desactivada(cliente):
    respuesta = login(cliente, "66666666-6", CLAVE_PROFESIONAL)
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["codigo"] == "credenciales_invalidas"


def test_me_sin_token(cliente):
    respuesta = cliente.get("/api/v1/auth/me")
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["codigo"] == "no_autenticado"


def test_me_con_token_invalido(cliente):
    respuesta = cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer no-es-un-token"},
    )
    assert respuesta.status_code == 401


def test_me_con_token_expirado(cliente):
    token, _ = crear_token_acceso(
        "11111111-1", "administrador", expira_en_minutos=-5
    )
    respuesta = cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["codigo"] == "no_autenticado"


def test_me_con_token_de_usuario_inexistente(cliente):
    token, _ = crear_token_acceso("99999999-9", "administrador")
    respuesta = cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 401


@pytest.mark.parametrize(
    ("rut", "password", "rol"),
    [
        ("11111111-1", CLAVE_ADMIN, "administrador"),
        ("22222222-2", CLAVE_PROFESIONAL, "profesional"),
    ],
)
def test_me_devuelve_la_identidad(cliente, rut, password, rol):
    token = token_de(cliente, rut, password)
    respuesta = cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["rut"] == rut
    assert cuerpo["rol"] == rol
    assert "password_hash" not in cuerpo
    assert "password" not in json.dumps(cuerpo).lower()


def test_cuenta_desactivada_pierde_acceso_aunque_el_token_siga_vigente(
    cliente, conexion
):
    token = token_de(cliente, "11111111-1", CLAVE_ADMIN)
    conexion.execute(
        text("UPDATE usuarios SET activo = false WHERE rut = '11111111-1'")
    )

    respuesta = cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 401


def test_el_token_no_contiene_datos_sensibles():
    token, _ = crear_token_acceso("11111111-1", "administrador")
    payload = jwt.decode(token, options={"verify_signature": False})

    assert set(payload) == {"sub", "rol", "iat", "exp"}
    assert "password" not in json.dumps(payload).lower()
    assert "registro" not in json.dumps(payload).lower()


def test_hash_es_argon2id():
    hash_generado = hashear_password("ClaveSegura123")

    assert hash_generado.startswith("$argon2id$")
    assert verificar_password("ClaveSegura123", hash_generado) is True
    assert verificar_password("ClaveSegura124", hash_generado) is False


def test_permisos_de_roles_por_http(usuarios_auth, cliente, conexion):
    token_admin = token_de(cliente, "11111111-1", CLAVE_ADMIN)
    token_profesional = token_de(cliente, "22222222-2", CLAVE_PROFESIONAL)

    app_prueba = FastAPI()
    registrar_manejadores(app_prueba)

    @app_prueba.get("/solo-admin")
    def _solo_admin(
        usuario: Usuario = Depends(requiere_roles(RolUsuario.ADMINISTRADOR)),
    ):
        return {"rut": usuario.rut}

    @app_prueba.get("/solo-profesional")
    def _solo_profesional(
        usuario: Usuario = Depends(requiere_roles(RolUsuario.PROFESIONAL)),
    ):
        return {"rut": usuario.rut}

    app_prueba.dependency_overrides[get_db] = _override_db(conexion)

    def cabecera(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    with TestClient(app_prueba) as prueba:
        assert prueba.get("/solo-admin", headers=cabecera(token_admin)).status_code == 200
        prohibido = prueba.get("/solo-admin", headers=cabecera(token_profesional))
        assert prohibido.status_code == 403
        assert prohibido.json()["error"]["codigo"] == "sin_permisos"

        assert (
            prueba.get(
                "/solo-profesional", headers=cabecera(token_profesional)
            ).status_code
            == 200
        )
        assert (
            prueba.get("/solo-profesional", headers=cabecera(token_admin)).status_code
            == 403
        )
