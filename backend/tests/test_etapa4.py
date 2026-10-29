"""Pruebas de usuarios, profesionales y pacientes (Etapa 4)."""

import json
from datetime import date, timedelta

import pytest

from tests.apoyo import CLAVE_ADMIN, CLAVE_PROFESIONAL, cabecera, login, token_de


@pytest.fixture()
def tokens(cliente):
    return {
        "admin": token_de(cliente, "11111111-1", CLAVE_ADMIN),
        "profesional": token_de(cliente, "22222222-2", CLAVE_PROFESIONAL),
    }


def datos_usuario(**extra):
    base = {
        "rut": "12345678-5",
        "nombres": "Nora",
        "apellidos": "Nueva",
        "correo_electronico": "nora@ejemplo.cl",
        "password": "ClaveNueva123!",
        "rol": "profesional",
    }
    base.update(extra)
    return base


def datos_profesional(**extra):
    base = {
        "rut": "77777777-7",
        "nombres": "Rita",
        "apellidos": "Nueva",
        "especialidad": "Nutricion",
        "telefono": "+56922222222",
        "correo_electronico": "rita@ejemplo.cl",
    }
    base.update(extra)
    return base


def datos_paciente(**extra):
    base = {
        "rut": "99999999-9",
        "nombres": "Sofia",
        "apellidos": "Sintetica",
        "fecha_nacimiento": "1992-03-15",
        "telefono": "+56911111111",
        "correo_electronico": "sofia@ejemplo.cl",
        "direccion": "Pasaje Falso 789",
    }
    base.update(extra)
    return base


# --- Usuarios -----------------------------------------------------------------


def test_admin_crea_usuario_y_ese_usuario_puede_iniciar_sesion(cliente, tokens):
    respuesta = cliente.post(
        "/api/v1/usuarios",
        json=datos_usuario(),
        headers=cabecera(tokens["admin"]),
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["rut"] == "12345678-5"
    assert cuerpo["rol"] == "profesional"
    assert "password" not in json.dumps(cuerpo).lower()

    acceso = login(cliente, "12.345.678-5", "ClaveNueva123!")
    assert acceso.status_code == 200
    assert acceso.json()["usuario"]["rol"] == "profesional"


def test_usuario_duplicado_es_conflicto(cliente, tokens):
    cliente.post(
        "/api/v1/usuarios",
        json=datos_usuario(),
        headers=cabecera(tokens["admin"]),
    )
    respuesta = cliente.post(
        "/api/v1/usuarios",
        json=datos_usuario(),
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 409


def test_usuario_con_rut_invalido_es_rechazado(cliente, tokens):
    respuesta = cliente.post(
        "/api/v1/usuarios",
        json=datos_usuario(rut="12.345.678-9"),
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "datos_invalidos"


def test_profesional_no_puede_gestionar_usuarios(cliente, tokens):
    cabeceras = cabecera(tokens["profesional"])

    assert cliente.get("/api/v1/usuarios", headers=cabeceras).status_code == 403
    assert (
        cliente.post(
            "/api/v1/usuarios", json=datos_usuario(), headers=cabeceras
        ).status_code
        == 403
    )
    assert (
        cliente.get("/api/v1/usuarios/11111111-1", headers=cabeceras).status_code
        == 403
    )
    assert (
        cliente.patch(
            "/api/v1/usuarios/11111111-1",
            json={"nombres": "Intruso"},
            headers=cabeceras,
        ).status_code
        == 403
    )


def test_cambio_de_rol_se_aplica_de_inmediato(cliente, tokens):
    cliente.post(
        "/api/v1/usuarios",
        json=datos_usuario(),
        headers=cabecera(tokens["admin"]),
    )
    token_usuario = token_de(cliente, "12345678-5", "ClaveNueva123!")

    respuesta = cliente.patch(
        "/api/v1/usuarios/12345678-5",
        json={"rol": "administrador"},
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "administrador"

    identidad = cliente.get(
        "/api/v1/auth/me", headers=cabecera(token_usuario)
    )
    assert identidad.status_code == 200
    assert identidad.json()["rol"] == "administrador"


def test_listado_de_usuarios_pagina_y_busca(cliente, tokens):
    cabeceras = cabecera(tokens["admin"])
    cliente.post("/api/v1/usuarios", json=datos_usuario(), headers=cabeceras)
    cliente.post(
        "/api/v1/usuarios",
        json=datos_usuario(rut="88888888-8", correo_electronico="otro@ejemplo.cl"),
        headers=cabeceras,
    )

    pagina = cliente.get(
        "/api/v1/usuarios?page=1&per_page=2", headers=cabeceras
    ).json()
    assert len(pagina["items"]) == 2
    assert pagina["total"] >= 5
    assert pagina["pages"] >= 3

    busqueda = cliente.get(
        "/api/v1/usuarios?rut=12.345.678", headers=cabeceras
    ).json()
    assert busqueda["total"] == 1
    assert busqueda["items"][0]["rut"] == "12345678-5"

    solo_admins = cliente.get(
        "/api/v1/usuarios?rol=administrador", headers=cabeceras
    ).json()
    assert solo_admins["total"] >= 1
    assert all(item["rol"] == "administrador" for item in solo_admins["items"])


def test_usuario_inexistente_devuelve_404(cliente, tokens):
    respuesta = cliente.get(
        "/api/v1/usuarios/12345678-5",
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 404


# --- Profesionales ------------------------------------------------------------


def test_admin_crea_profesional(cliente, tokens):
    respuesta = cliente.post(
        "/api/v1/profesionales",
        json=datos_profesional(),
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["rut"] == "77777777-7"
    assert cuerpo["usuario_rut"] is None


def test_profesional_no_puede_crear_ni_modificar_perfiles(cliente, tokens):
    cabeceras = cabecera(tokens["profesional"])

    assert (
        cliente.post(
            "/api/v1/profesionales", json=datos_profesional(), headers=cabeceras
        ).status_code
        == 403
    )
    assert (
        cliente.patch(
            "/api/v1/profesionales/22222222-2",
            json={"especialidad": "Otra"},
            headers=cabeceras,
        ).status_code
        == 403
    )


def test_profesional_duplicado_es_conflicto(cliente, tokens):
    cabeceras = cabecera(tokens["admin"])
    cliente.post("/api/v1/profesionales", json=datos_profesional(), headers=cabeceras)
    respuesta = cliente.post(
        "/api/v1/profesionales", json=datos_profesional(), headers=cabeceras
    )
    assert respuesta.status_code == 409


def test_profesional_no_puede_vincular_una_cuenta_con_otro_rut(cliente, tokens):
    respuesta = cliente.post(
        "/api/v1/profesionales",
        json=datos_profesional(usuario_rut="11111111-1"),
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 422


def test_profesional_no_puede_vincular_una_cuenta_administradora(cliente, tokens):
    respuesta = cliente.post(
        "/api/v1/profesionales",
        json=datos_profesional(rut="11111111-1", usuario_rut="11111111-1"),
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 409


def test_vinculacion_correcta_con_cuenta_profesional(cliente, tokens):
    cabeceras = cabecera(tokens["admin"])

    alta_cuenta = cliente.post(
        "/api/v1/usuarios",
        json=datos_usuario(rut="77777777-7", correo_electronico="rita@ejemplo.cl"),
        headers=cabeceras,
    )
    assert alta_cuenta.status_code == 201

    respuesta = cliente.post(
        "/api/v1/profesionales",
        json=datos_profesional(usuario_rut="77777777-7"),
        headers=cabeceras,
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["usuario_rut"] == "77777777-7"


def test_ambos_roles_pueden_consultar_profesionales(cliente, tokens):
    cabeceras = cabecera(tokens["profesional"])

    listado = cliente.get("/api/v1/profesionales", headers=cabeceras)
    assert listado.status_code == 200
    assert listado.json()["total"] >= 2

    detalle = cliente.get("/api/v1/profesionales/22222222-2", headers=cabeceras)
    assert detalle.status_code == 200
    assert detalle.json()["especialidad"] == "Psicologia"


def test_rut_del_profesional_se_normaliza(cliente, tokens):
    respuesta = cliente.post(
        "/api/v1/profesionales",
        json=datos_profesional(rut="88.888.888-8"),
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["rut"] == "88888888-8"


# --- Pacientes ----------------------------------------------------------------


def test_admin_crea_paciente_y_normaliza_el_rut(cliente, tokens):
    respuesta = cliente.post(
        "/api/v1/pacientes",
        json=datos_paciente(rut="99.999.999-9"),
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["rut"] == "99999999-9"


def test_profesional_no_puede_crear_pacientes(cliente, tokens):
    respuesta = cliente.post(
        "/api/v1/pacientes",
        json=datos_paciente(),
        headers=cabecera(tokens["profesional"]),
    )
    assert respuesta.status_code == 403


def test_paciente_duplicado_es_conflicto(cliente, tokens):
    cabeceras = cabecera(tokens["admin"])
    cliente.post("/api/v1/pacientes", json=datos_paciente(), headers=cabeceras)
    respuesta = cliente.post(
        "/api/v1/pacientes", json=datos_paciente(), headers=cabeceras
    )
    assert respuesta.status_code == 409


def test_paciente_con_digito_verificador_invalido_es_rechazado(cliente, tokens):
    respuesta = cliente.post(
        "/api/v1/pacientes",
        json=datos_paciente(rut="12.345.678-9"),
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 422


def test_paciente_con_fecha_de_nacimiento_futura_es_rechazado(cliente, tokens):
    manana = (date.today() + timedelta(days=1)).isoformat()
    respuesta = cliente.post(
        "/api/v1/pacientes",
        json=datos_paciente(fecha_nacimiento=manana),
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 422


def test_ambos_roles_pueden_consultar_pacientes(cliente, tokens):
    cabeceras = cabecera(tokens["profesional"])

    listado = cliente.get("/api/v1/pacientes?rut=33.333.333", headers=cabeceras)
    assert listado.status_code == 200
    assert listado.json()["total"] == 1

    detalle = cliente.get("/api/v1/pacientes/33333333-3", headers=cabeceras)
    assert detalle.status_code == 200
    assert detalle.json()["nombres"] == "Paula"


def test_profesional_no_puede_modificar_ni_eliminar_pacientes(cliente, tokens):
    cabeceras = cabecera(tokens["profesional"])

    assert (
        cliente.patch(
            "/api/v1/pacientes/33333333-3",
            json={"direccion": "Otra direccion"},
            headers=cabeceras,
        ).status_code
        == 403
    )
    assert (
        cliente.delete(
            "/api/v1/pacientes/33333333-3", headers=cabeceras
        ).status_code
        == 403
    )


def test_admin_modifica_paciente(cliente, tokens):
    respuesta = cliente.patch(
        "/api/v1/pacientes/33333333-3",
        json={"direccion": "Nueva direccion 999"},
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["direccion"] == "Nueva direccion 999"


def test_eliminar_paciente_sin_historial(cliente, tokens):
    cabeceras = cabecera(tokens["admin"])
    cliente.post("/api/v1/pacientes", json=datos_paciente(), headers=cabeceras)

    borrado = cliente.delete("/api/v1/pacientes/99999999-9", headers=cabeceras)
    assert borrado.status_code == 204
    assert borrado.content == b""

    assert (
        cliente.get("/api/v1/pacientes/99999999-9", headers=cabeceras).status_code
        == 404
    )


def test_no_eliminar_paciente_con_historial(cliente, tokens, crear_cita):
    crear_cita(paciente="33333333-3")

    respuesta = cliente.delete(
        "/api/v1/pacientes/33333333-3",
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 409
    error = respuesta.json()["error"]
    assert error["codigo"] == "conflicto"
    assert "historial" in error["mensaje"].lower()


def test_busqueda_de_pacientes_por_rut_parcial(cliente, tokens):
    respuesta = cliente.get(
        "/api/v1/pacientes?rut=44.444.444",
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 1
    assert respuesta.json()["items"][0]["rut"] == "44444444-4"
