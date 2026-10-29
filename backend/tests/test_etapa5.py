"""Pruebas de citas y agenda (Etapa 5)."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text

from tests.apoyo import CLAVE_ADMIN, CLAVE_PROFESIONAL, cabecera, token_de


@pytest.fixture()
def tokens(cliente):
    return {
        "admin": token_de(cliente, "11111111-1", CLAVE_ADMIN),
        "profesional": token_de(cliente, "22222222-2", CLAVE_PROFESIONAL),
    }


def datos_cita(**extra):
    base = {
        "paciente_rut": "33.333.333-3",
        "fecha_hora_inicio": "2026-12-01T09:00:00",
        "fecha_hora_fin": "2026-12-01T09:30:00",
        "motivo": "Consulta de control",
    }
    base.update(extra)
    return base


def crear(cliente, tokens, **extra):
    return cliente.post(
        "/api/v1/citas",
        json=datos_cita(**extra),
        headers=cabecera(tokens["profesional"]),
    )


def test_profesional_crea_cita_para_si_mismo(cliente, tokens):
    respuesta = crear(cliente, tokens)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["profesional_rut"] == "22222222-2"
    assert cuerpo["paciente_rut"] == "33333333-3"
    assert cuerpo["creado_por_rut"] == "22222222-2"
    assert cuerpo["estado"] == "pendiente"
    assert cuerpo["fecha_hora_inicio"] == "2026-12-01T09:00:00-03:00"
    assert cuerpo["fecha_hora_fin"] == "2026-12-01T09:30:00-03:00"


@pytest.mark.parametrize(
    "campo",
    [{"profesional_rut": "55555555-5"}, {"estado": "confirmada"}],
)
def test_el_cuerpo_no_permite_fijar_datos_del_servidor(cliente, tokens, campo):
    respuesta = crear(cliente, tokens, **campo)

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "datos_invalidos"


def test_administrador_no_puede_crear_citas(cliente, tokens):
    respuesta = cliente.post(
        "/api/v1/citas",
        json=datos_cita(),
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["codigo"] == "sin_permisos"


@pytest.mark.parametrize(
    ("inicio", "fin"),
    [
        ("2026-12-01T09:00:00", "2026-12-01T09:00:00"),
        ("2026-12-01T09:30:00", "2026-12-01T09:00:00"),
    ],
)
def test_horario_invalido_es_rechazado(cliente, tokens, inicio, fin):
    respuesta = crear(
        cliente, tokens, fecha_hora_inicio=inicio, fecha_hora_fin=fin
    )
    assert respuesta.status_code == 422


def test_solapamiento_es_conflicto_y_horario_contiguo_se_permite(cliente, tokens):
    assert crear(cliente, tokens).status_code == 201

    solapada = crear(
        cliente,
        tokens,
        fecha_hora_inicio="2026-12-01T09:15:00",
        fecha_hora_fin="2026-12-01T09:45:00",
    )
    assert solapada.status_code == 409
    assert solapada.json()["error"]["codigo"] == "conflicto"

    contigua = crear(
        cliente,
        tokens,
        fecha_hora_inicio="2026-12-01T09:30:00",
        fecha_hora_fin="2026-12-01T10:00:00",
    )
    assert contigua.status_code == 201


def test_cancelar_libera_el_horario(cliente, tokens):
    primera = crear(cliente, tokens)
    assert primera.status_code == 201

    cancelada = cliente.post(
        f"/api/v1/citas/{primera.json()['id_cita']}/cancelar",
        headers=cabecera(tokens["profesional"]),
    )
    assert cancelada.status_code == 200
    assert cancelada.json()["estado"] == "cancelada"

    segunda = crear(cliente, tokens)
    assert segunda.status_code == 201
    assert segunda.json()["id_cita"] != primera.json()["id_cita"]


def test_transiciones_validas(cliente, tokens):
    creada = crear(cliente, tokens).json()
    cabeceras = cabecera(tokens["profesional"])

    confirmada = cliente.post(
        f"/api/v1/citas/{creada['id_cita']}/confirmar", headers=cabeceras
    )
    assert confirmada.status_code == 200
    assert confirmada.json()["estado"] == "confirmada"

    ausente = cliente.post(
        f"/api/v1/citas/{creada['id_cita']}/ausente", headers=cabeceras
    )
    assert ausente.status_code == 200
    assert ausente.json()["estado"] == "ausente"


def test_pendiente_no_puede_marcarse_ausente(cliente, tokens):
    creada = crear(cliente, tokens).json()

    respuesta = cliente.post(
        f"/api/v1/citas/{creada['id_cita']}/ausente",
        headers=cabecera(tokens["profesional"]),
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["codigo"] == "conflicto"


@pytest.mark.parametrize("accion", ["confirmar", "cancelar", "ausente"])
def test_estado_terminal_no_cambia(cliente, tokens, accion):
    creada = crear(cliente, tokens).json()
    cabeceras = cabecera(tokens["profesional"])
    cliente.post(f"/api/v1/citas/{creada['id_cita']}/cancelar", headers=cabeceras)

    respuesta = cliente.post(
        f"/api/v1/citas/{creada['id_cita']}/{accion}", headers=cabeceras
    )
    assert respuesta.status_code == 409


def test_confirmar_dos_veces_es_conflicto(cliente, tokens):
    creada = crear(cliente, tokens).json()
    cabeceras = cabecera(tokens["profesional"])

    assert (
        cliente.post(
            f"/api/v1/citas/{creada['id_cita']}/confirmar", headers=cabeceras
        ).status_code
        == 200
    )
    repetida = cliente.post(
        f"/api/v1/citas/{creada['id_cita']}/confirmar", headers=cabeceras
    )
    assert repetida.status_code == 409


def test_administrador_ve_todas_y_profesional_solo_las_suyas(
    cliente, tokens, crear_cita
):
    assert crear(cliente, tokens).status_code == 201
    crear_cita(
        profesional="55555555-5",
        inicio=datetime(2026, 12, 2, 13, 0, tzinfo=timezone.utc),
        fin=datetime(2026, 12, 2, 13, 30, tzinfo=timezone.utc),
    )

    todas = cliente.get("/api/v1/citas", headers=cabecera(tokens["admin"]))
    assert todas.status_code == 200
    assert todas.json()["total"] == 2

    propias = cliente.get(
        "/api/v1/citas", headers=cabecera(tokens["profesional"])
    )
    assert propias.status_code == 200
    assert propias.json()["total"] == 1
    assert propias.json()["items"][0]["profesional_rut"] == "22222222-2"


def test_profesional_no_accede_a_cita_ajena(cliente, tokens, crear_cita):
    ajena = str(
        crear_cita(
            profesional="55555555-5",
            inicio=datetime(2026, 12, 2, 13, 0, tzinfo=timezone.utc),
            fin=datetime(2026, 12, 2, 13, 30, tzinfo=timezone.utc),
        )
    )
    cabeceras = cabecera(tokens["profesional"])

    assert (
        cliente.get(f"/api/v1/citas/{ajena}", headers=cabeceras).status_code
        == 404
    )
    assert (
        cliente.post(
            f"/api/v1/citas/{ajena}/confirmar", headers=cabeceras
        ).status_code
        == 404
    )


@pytest.mark.parametrize("accion", ["confirmar", "cancelar", "ausente"])
def test_administrador_no_cambia_el_estado(cliente, tokens, crear_cita, accion):
    creada = str(
        crear_cita(
            inicio=datetime(2026, 12, 2, 13, 0, tzinfo=timezone.utc),
            fin=datetime(2026, 12, 2, 13, 30, tzinfo=timezone.utc),
        )
    )

    respuesta = cliente.post(
        f"/api/v1/citas/{creada}/{accion}", headers=cabecera(tokens["admin"])
    )
    assert respuesta.status_code == 403


def test_filtros_por_paciente_estado_y_rango(cliente, tokens):
    primera = crear(cliente, tokens)
    assert primera.status_code == 201

    segunda = crear(
        cliente,
        tokens,
        paciente_rut="44.444.444-4",
        fecha_hora_inicio="2026-12-05T09:00:00",
        fecha_hora_fin="2026-12-05T09:30:00",
    )
    assert segunda.status_code == 201

    cliente.post(
        f"/api/v1/citas/{primera.json()['id_cita']}/cancelar",
        headers=cabecera(tokens["profesional"]),
    )
    cabeceras = cabecera(tokens["admin"])

    por_paciente = cliente.get(
        "/api/v1/citas?paciente_rut=44.444.444", headers=cabeceras
    ).json()
    assert por_paciente["total"] == 1
    assert por_paciente["items"][0]["paciente_rut"] == "44444444-4"

    por_estado = cliente.get(
        "/api/v1/citas?estado=cancelada", headers=cabeceras
    ).json()
    assert por_estado["total"] == 1
    assert por_estado["items"][0]["estado"] == "cancelada"

    por_rango = cliente.get(
        "/api/v1/citas?desde=2026-12-04&hasta=2026-12-06", headers=cabeceras
    ).json()
    assert por_rango["total"] == 1
    assert por_rango["items"][0]["paciente_rut"] == "44444444-4"


def test_paginacion_en_servidor(cliente, tokens):
    for inicio, fin in (
        ("2026-12-01T09:00:00", "2026-12-01T09:30:00"),
        ("2026-12-01T10:00:00", "2026-12-01T10:30:00"),
        ("2026-12-01T11:00:00", "2026-12-01T11:30:00"),
    ):
        assert (
            crear(
                cliente,
                tokens,
                fecha_hora_inicio=inicio,
                fecha_hora_fin=fin,
            ).status_code
            == 201
        )

    pagina = cliente.get(
        "/api/v1/citas?page=1&per_page=2", headers=cabecera(tokens["admin"])
    ).json()
    assert len(pagina["items"]) == 2
    assert pagina["total"] == 3
    assert pagina["pages"] == 2

    segunda = cliente.get(
        "/api/v1/citas?page=2&per_page=2", headers=cabecera(tokens["admin"])
    ).json()
    assert len(segunda["items"]) == 1


def test_observaciones_solo_las_edita_el_administrador(cliente, tokens, crear_cita):
    cita = str(
        crear_cita(
            inicio=datetime(2026, 12, 2, 13, 0, tzinfo=timezone.utc),
            fin=datetime(2026, 12, 2, 13, 30, tzinfo=timezone.utc),
        )
    )

    prohibido = cliente.patch(
        f"/api/v1/citas/{cita}/observaciones",
        json={"observaciones_administrativas": "Nota"},
        headers=cabecera(tokens["profesional"]),
    )
    assert prohibido.status_code == 403

    editada = cliente.patch(
        f"/api/v1/citas/{cita}/observaciones",
        json={"observaciones_administrativas": "Reprogramacion pendiente"},
        headers=cabecera(tokens["admin"]),
    )
    assert editada.status_code == 200
    cuerpo = editada.json()
    assert cuerpo["observaciones_administrativas"] == "Reprogramacion pendiente"
    assert cuerpo["motivo"] == "Consulta de prueba"

    solo_ese_campo = cliente.patch(
        f"/api/v1/citas/{cita}/observaciones",
        json={"motivo": "Otro motivo"},
        headers=cabecera(tokens["admin"]),
    )
    assert solo_ese_campo.status_code == 422


def test_paciente_inactivo_no_puede_agendar(cliente, tokens, conexion):
    conexion.execute(
        text("UPDATE pacientes SET activo = false WHERE rut = '33333333-3'")
    )

    respuesta = crear(cliente, tokens)
    assert respuesta.status_code == 409
    assert "inactivo" in respuesta.json()["error"]["mensaje"].lower()


def test_profesional_sin_perfil_no_puede_agendar(cliente, tokens):
    alta = cliente.post(
        "/api/v1/usuarios",
        json={
            "rut": "77777777-7",
            "nombres": "Sin",
            "apellidos": "Perfil",
            "correo_electronico": "sinperfil@example.com",
            "password": "ClaveNueva123!",
            "rol": "profesional",
        },
        headers=cabecera(tokens["admin"]),
    )
    assert alta.status_code == 201

    token = token_de(cliente, "77777777-7", "ClaveNueva123!")
    respuesta = cliente.post(
        "/api/v1/citas",
        json=datos_cita(),
        headers=cabecera(token),
    )
    assert respuesta.status_code == 409
    assert "perfil profesional" in respuesta.json()["error"]["mensaje"]


def test_cita_inexistente_devuelve_404(cliente, tokens):
    inexistente = uuid4()

    assert (
        cliente.get(
            f"/api/v1/citas/{inexistente}",
            headers=cabecera(tokens["admin"]),
        ).status_code
        == 404
    )
    assert (
        cliente.post(
            f"/api/v1/citas/{inexistente}/confirmar",
            headers=cabecera(tokens["profesional"]),
        ).status_code
        == 404
    )


def test_la_restriccion_de_la_base_frena_un_solapamiento_concurrente(
    cliente, tokens, crear_cita, monkeypatch
):
    """Sin la comprobacion previa, el EXCLUDE de PostgreSQL sigue protegiendo."""
    inicio = datetime(2026, 12, 2, 13, 0, tzinfo=timezone.utc)
    fin = datetime(2026, 12, 2, 13, 30, tzinfo=timezone.utc)
    crear_cita(inicio=inicio, fin=fin)
    monkeypatch.setattr(
        "app.services.citas._hay_solapamiento", lambda *args, **kwargs: False
    )

    respuesta = crear(
        cliente,
        tokens,
        fecha_hora_inicio="2026-12-02T10:00:00",
        fecha_hora_fin="2026-12-02T10:30:00",
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["codigo"] == "conflicto"


def test_horarios_se_presentan_en_hora_de_santiago(cliente, tokens):
    con_offset = crear(
        cliente,
        tokens,
        fecha_hora_inicio="2026-12-02T12:00:00Z",
        fecha_hora_fin="2026-12-02T12:30:00Z",
    )
    assert con_offset.status_code == 201
    assert con_offset.json()["fecha_hora_inicio"] == (
        "2026-12-02T09:00:00-03:00"
    )

    detalle = cliente.get(
        f"/api/v1/citas/{con_offset.json()['id_cita']}",
        headers=cabecera(tokens["admin"]),
    ).json()
    assert detalle["fecha_hora_inicio"].endswith("-03:00")
