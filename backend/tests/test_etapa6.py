"""Pruebas de atenciones (Etapa 6)."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from tests.apoyo import CLAVE_ADMIN, CLAVE_PROFESIONAL, cabecera, token_de

INICIO = datetime(2026, 12, 2, 13, 0, tzinfo=timezone.utc)
FIN = datetime(2026, 12, 2, 13, 30, tzinfo=timezone.utc)


@pytest.fixture()
def tokens(cliente):
    return {
        "admin": token_de(cliente, "11111111-1", CLAVE_ADMIN),
        "profesional": token_de(cliente, "22222222-2", CLAVE_PROFESIONAL),
    }


def datos_atencion(id_cita, **extra):
    base = {
        "id_cita": str(id_cita),
        "fecha_atencion": "2026-12-02T10:10:00",
        "motivo": "Control de seguimiento",
        "registro_clinico": "Paciente estable, sin signos de alarma.",
    }
    base.update(extra)
    return base


def registrar(cliente, tokens, id_cita, **extra):
    return cliente.post(
        "/api/v1/atenciones",
        json=datos_atencion(id_cita, **extra),
        headers=cabecera(tokens["profesional"]),
    )


def test_registrar_atencion_cierra_la_cita(cliente, tokens, crear_cita):
    cita = str(crear_cita(estado="confirmada", inicio=INICIO, fin=FIN))

    respuesta = registrar(cliente, tokens, cita)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["id_cita"] == cita
    assert cuerpo["paciente_rut"] == "33333333-3"
    assert cuerpo["profesional_rut"] == "22222222-2"
    assert cuerpo["creado_por_rut"] == "22222222-2"
    assert cuerpo["fecha_atencion"] == "2026-12-02T10:10:00-03:00"

    detalle = cliente.get(
        f"/api/v1/citas/{cita}", headers=cabecera(tokens["admin"])
    ).json()
    assert detalle["estado"] == "atendida"


@pytest.mark.parametrize("estado", ["pendiente", "cancelada", "atendida"])
def test_solo_una_cita_confirmada_admite_atencion(
    cliente, tokens, crear_cita, estado
):
    cita = str(crear_cita(estado=estado, inicio=INICIO, fin=FIN))

    respuesta = registrar(cliente, tokens, cita)

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["codigo"] == "conflicto"


def test_fallo_de_insercion_no_deja_la_cita_atendida(
    cliente, tokens, crear_cita, crear_atencion, conexion
):
    cita = str(crear_cita(estado="confirmada", inicio=INICIO, fin=FIN))
    crear_atencion(id_cita=cita)

    respuesta = registrar(cliente, tokens, cita)

    assert respuesta.status_code == 409
    desde_api = cliente.get(
        f"/api/v1/citas/{cita}", headers=cabecera(tokens["admin"])
    ).json()
    assert desde_api["estado"] == "confirmada"
    assert (
        cliente.get(
            "/api/v1/atenciones", headers=cabecera(tokens["admin"])
        ).json()["total"]
        == 1
    )


def test_no_se_registra_atencion_de_una_cita_ajena(cliente, tokens, crear_cita):
    cita = str(
        crear_cita(profesional="55555555-5", estado="confirmada", inicio=INICIO, fin=FIN)
    )

    respuesta = registrar(cliente, tokens, cita)

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["codigo"] == "no_encontrado"


def test_administrador_no_registra_atenciones(cliente, tokens, crear_cita):
    cita = str(crear_cita(estado="confirmada", inicio=INICIO, fin=FIN))

    respuesta = cliente.post(
        "/api/v1/atenciones",
        json=datos_atencion(cita),
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 403


def test_cita_inexistente_devuelve_404(cliente, tokens):
    respuesta = registrar(cliente, tokens, uuid4())
    assert respuesta.status_code == 404


@pytest.mark.parametrize(
    "fecha",
    ["2026-12-02T09:00:00", "2026-12-02T11:00:00"],
)
def test_fecha_fuera_del_horario_es_rechazada(
    cliente, tokens, crear_cita, fecha
):
    cita = str(crear_cita(estado="confirmada", inicio=INICIO, fin=FIN))

    respuesta = registrar(cliente, tokens, cita, fecha_atencion=fecha)

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "datos_invalidos"


def test_profesional_corrige_su_atencion(cliente, tokens, crear_cita):
    cita = str(crear_cita(estado="confirmada", inicio=INICIO, fin=FIN))
    creada = registrar(cliente, tokens, cita).json()
    cabeceras = cabecera(tokens["profesional"])

    respuesta = cliente.patch(
        f"/api/v1/atenciones/{creada['id_atencion']}",
        json={
            "motivo": "Control corregido",
            "registro_clinico": "Se corrige el registro: paciente estable.",
        },
        headers=cabeceras,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["motivo"] == "Control corregido"
    assert respuesta.json()["registro_clinico"].startswith("Se corrige")
    assert respuesta.json()["paciente_rut"] == "33333333-3"


def test_no_se_corrige_una_atencion_ajena(
    cliente, tokens, crear_cita, crear_atencion
):
    cita = str(
        crear_cita(
            profesional="55555555-5", estado="atendida", inicio=INICIO, fin=FIN
        )
    )
    ajena = str(crear_atencion(id_cita=cita, profesional="55555555-5"))

    respuesta = cliente.patch(
        f"/api/v1/atenciones/{ajena}",
        json={"motivo": "Intento"},
        headers=cabecera(tokens["profesional"]),
    )
    assert respuesta.status_code == 404

    admin = cliente.patch(
        f"/api/v1/atenciones/{ajena}",
        json={"motivo": "Intento"},
        headers=cabecera(tokens["admin"]),
    )
    assert admin.status_code == 403


def test_listado_por_rol_y_filtros(cliente, tokens, crear_cita, crear_atencion):
    cita_uno = str(crear_cita(estado="confirmada", inicio=INICIO, fin=FIN))
    assert registrar(cliente, tokens, cita_uno).status_code == 201

    inicio_dos = datetime(2026, 12, 5, 13, 0, tzinfo=timezone.utc)
    fin_dos = datetime(2026, 12, 5, 13, 30, tzinfo=timezone.utc)
    cita_dos = str(
        crear_cita(
            paciente="44444444-4",
            estado="confirmada",
            inicio=inicio_dos,
            fin=fin_dos,
        )
    )
    assert (
        registrar(
            cliente,
            tokens,
            cita_dos,
            fecha_atencion="2026-12-05T10:10:00",
        ).status_code
        == 201
    )

    cita_tres = str(
        crear_cita(
            profesional="55555555-5",
            estado="atendida",
            inicio=INICIO,
            fin=FIN,
        )
    )
    crear_atencion(id_cita=cita_tres, profesional="55555555-5")

    todas = cliente.get("/api/v1/atenciones", headers=cabecera(tokens["admin"]))
    assert todas.status_code == 200
    assert todas.json()["total"] == 3

    propias = cliente.get(
        "/api/v1/atenciones", headers=cabecera(tokens["profesional"])
    )
    assert propias.json()["total"] == 2
    assert all(
        item["profesional_rut"] == "22222222-2"
        for item in propias.json()["items"]
    )

    por_paciente = cliente.get(
        "/api/v1/atenciones?paciente_rut=44.444.444",
        headers=cabecera(tokens["admin"]),
    ).json()
    assert por_paciente["total"] == 1
    assert por_paciente["items"][0]["paciente_rut"] == "44444444-4"

    por_rango = cliente.get(
        "/api/v1/atenciones?desde=2026-12-04&hasta=2026-12-06",
        headers=cabecera(tokens["admin"]),
    ).json()
    assert por_rango["total"] == 1
    assert por_rango["items"][0]["paciente_rut"] == "44444444-4"


def test_detalle_solo_para_el_dueno_o_el_administrador(
    cliente, tokens, crear_cita, crear_atencion
):
    cita = str(
        crear_cita(
            profesional="55555555-5", estado="atendida", inicio=INICIO, fin=FIN
        )
    )
    ajena = str(crear_atencion(id_cita=cita, profesional="55555555-5"))

    assert (
        cliente.get(
            f"/api/v1/atenciones/{ajena}",
            headers=cabecera(tokens["admin"]),
        ).status_code
        == 200
    )
    assert (
        cliente.get(
            f"/api/v1/atenciones/{ajena}",
            headers=cabecera(tokens["profesional"]),
        ).status_code
        == 404
    )


def test_el_cuerpo_no_permite_fijar_paciente_ni_profesional(
    cliente, tokens, crear_cita
):
    cita = str(crear_cita(estado="confirmada", inicio=INICIO, fin=FIN))

    respuesta = registrar(
        cliente, tokens, cita, profesional_rut="55555555-5"
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "datos_invalidos"
