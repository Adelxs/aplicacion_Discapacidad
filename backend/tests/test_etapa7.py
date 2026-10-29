"""Pruebas de documentos privados (Etapa 7)."""

from datetime import datetime, timezone

import pytest

from app.core.config import settings
from tests.apoyo import CLAVE_ADMIN, CLAVE_PROFESIONAL, cabecera, token_de

PDF = b"%PDF-1.4\nContenido sintetico de prueba.\n%%EOF\n"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
INICIO = datetime(2026, 12, 2, 13, 0, tzinfo=timezone.utc)
FIN = datetime(2026, 12, 2, 13, 30, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def almacen(tmp_path, monkeypatch):
    """Cada prueba usa un directorio temporal como volumen de documentos."""
    monkeypatch.setattr(settings, "documentos_dir", str(tmp_path))
    return tmp_path


@pytest.fixture()
def tokens(cliente):
    return {
        "admin": token_de(cliente, "11111111-1", CLAVE_ADMIN),
        "profesional": token_de(cliente, "22222222-2", CLAVE_PROFESIONAL),
    }


def subir(
    cliente,
    token,
    *,
    paciente="33.333.333-3",
    nombre="informe.pdf",
    contenido=PDF,
    tipo="application/pdf",
    id_atencion=None,
):
    datos = {"paciente_rut": paciente}
    if id_atencion is not None:
        datos["id_atencion"] = str(id_atencion)
    return cliente.post(
        "/api/v1/documentos",
        data=datos,
        files={"archivo": (nombre, contenido, tipo)},
        headers=cabecera(token),
    )


def test_administrador_sube_documento_del_paciente(cliente, tokens, almacen):
    respuesta = subir(cliente, tokens["admin"])

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["paciente_rut"] == "33333333-3"
    assert cuerpo["id_atencion"] is None
    assert cuerpo["nombre_original"] == "informe.pdf"
    assert cuerpo["tipo_mime"] == "application/pdf"
    assert cuerpo["tamano_bytes"] == len(PDF)
    assert cuerpo["subido_por_rut"] == "11111111-1"
    assert "clave_archivo" not in cuerpo
    assert len(list(almacen.iterdir())) == 1


def test_el_nombre_original_no_conserva_rutas(cliente, tokens):
    respuesta = subir(cliente, tokens["admin"], nombre="../../evil.pdf")

    assert respuesta.status_code == 201
    assert respuesta.json()["nombre_original"] == "evil.pdf"


def test_profesional_sube_a_su_atencion_y_descarga(
    cliente, tokens, crear_cita, crear_atencion
):
    cita = str(crear_cita(estado="atendida", inicio=INICIO, fin=FIN))
    atencion = str(crear_atencion(id_cita=cita))

    subido = subir(cliente, tokens["profesional"], id_atencion=atencion)
    assert subido.status_code == 201
    assert subido.json()["id_atencion"] == atencion

    descarga = cliente.get(
        f"/api/v1/documentos/{subido.json()['id_documento']}/archivo",
        headers=cabecera(tokens["profesional"]),
    )
    assert descarga.status_code == 200
    assert descarga.content == PDF
    assert descarga.headers["content-type"] == "application/pdf"
    assert "informe.pdf" in descarga.headers["content-disposition"]


def test_profesional_no_sube_a_una_atencion_ajena(
    cliente, tokens, crear_cita, crear_atencion, almacen
):
    cita = str(
        crear_cita(
            profesional="55555555-5", estado="atendida", inicio=INICIO, fin=FIN
        )
    )
    ajena = str(crear_atencion(id_cita=cita, profesional="55555555-5"))

    respuesta = subir(cliente, tokens["profesional"], id_atencion=ajena)

    assert respuesta.status_code == 404
    assert list(almacen.iterdir()) == []


def test_la_atencion_debe_corresponder_al_paciente(
    cliente, tokens, crear_cita, crear_atencion
):
    cita = str(crear_cita(estado="atendida", inicio=INICIO, fin=FIN))
    atencion = str(crear_atencion(id_cita=cita))

    respuesta = subir(
        cliente,
        tokens["profesional"],
        paciente="44.444.444-4",
        id_atencion=atencion,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "datos_invalidos"


def test_paciente_o_rut_invalido(cliente, tokens):
    assert subir(cliente, tokens["admin"], paciente="12.345.678-9").status_code == 422
    assert subir(cliente, tokens["admin"], paciente="99.999.999-9").status_code == 404


def test_tipo_y_contenido_no_permitidos(cliente, tokens, almacen):
    texto = subir(
        cliente,
        tokens["admin"],
        nombre="nota.txt",
        contenido=b"texto plano",
        tipo="text/plain",
    )
    assert texto.status_code == 415
    assert texto.json()["error"]["codigo"] == "tipo_no_permitido"

    disfrazado = subir(
        cliente,
        tokens["admin"],
        nombre="falso.pdf",
        contenido=b"esto no es un pdf",
        tipo="application/pdf",
    )
    assert disfrazado.status_code == 415

    assert list(almacen.iterdir()) == []


def test_tamano_maximo(cliente, tokens, almacen, monkeypatch):
    monkeypatch.setattr(settings, "max_documento_mb", 0)

    respuesta = subir(cliente, tokens["admin"])

    assert respuesta.status_code == 413
    assert respuesta.json()["error"]["codigo"] == "archivo_demasiado_grande"
    assert list(almacen.iterdir()) == []


def test_el_profesional_de_la_atencion_ve_lo_que_subio_el_admin(
    cliente, tokens, crear_cita, crear_atencion
):
    cita = str(crear_cita(estado="atendida", inicio=INICIO, fin=FIN))
    atencion = str(crear_atencion(id_cita=cita))
    subido = subir(cliente, tokens["admin"], id_atencion=atencion).json()

    metadatos = cliente.get(
        f"/api/v1/documentos/{subido['id_documento']}",
        headers=cabecera(tokens["profesional"]),
    )
    assert metadatos.status_code == 200

    descarga = cliente.get(
        f"/api/v1/documentos/{subido['id_documento']}/archivo",
        headers=cabecera(tokens["profesional"]),
    )
    assert descarga.status_code == 200
    assert descarga.content == PDF


def test_documento_ajeno_no_es_visible(
    cliente, tokens, crear_cita, crear_atencion
):
    cita = str(
        crear_cita(
            profesional="55555555-5", estado="atendida", inicio=INICIO, fin=FIN
        )
    )
    ajena = str(crear_atencion(id_cita=cita, profesional="55555555-5"))
    subido = subir(cliente, tokens["admin"], id_atencion=ajena).json()

    assert (
        cliente.get(
            f"/api/v1/documentos/{subido['id_documento']}",
            headers=cabecera(tokens["profesional"]),
        ).status_code
        == 404
    )

    listado = cliente.get(
        "/api/v1/documentos", headers=cabecera(tokens["profesional"])
    ).json()
    assert listado["total"] == 0


def test_solo_quien_subio_elimina(cliente, tokens, almacen):
    subido = subir(cliente, tokens["admin"]).json()
    ruta = f"/api/v1/documentos/{subido['id_documento']}"

    ajeno = cliente.delete(ruta, headers=cabecera(tokens["profesional"]))
    assert ajeno.status_code == 404

    borrado = cliente.delete(ruta, headers=cabecera(tokens["admin"]))
    assert borrado.status_code == 204
    assert borrado.content == b""

    assert (
        cliente.get(ruta, headers=cabecera(tokens["admin"])).status_code == 404
    )
    assert list(almacen.iterdir()) == []


def test_profesional_elimina_su_documento(cliente, tokens, almacen):
    subido = subir(cliente, tokens["profesional"]).json()

    borrado = cliente.delete(
        f"/api/v1/documentos/{subido['id_documento']}",
        headers=cabecera(tokens["profesional"]),
    )
    assert borrado.status_code == 204
    assert list(almacen.iterdir()) == []


def test_listado_por_rol_y_filtro_por_paciente(cliente, tokens):
    assert subir(cliente, tokens["admin"]).status_code == 201
    assert subir(cliente, tokens["profesional"]).status_code == 201
    assert (
        subir(cliente, tokens["admin"], paciente="44.444.444-4").status_code
        == 201
    )

    todas = cliente.get(
        "/api/v1/documentos", headers=cabecera(tokens["admin"])
    ).json()
    assert todas["total"] == 3

    propias = cliente.get(
        "/api/v1/documentos", headers=cabecera(tokens["profesional"])
    ).json()
    assert propias["total"] == 1

    filtradas = cliente.get(
        "/api/v1/documentos?paciente_rut=44.444.444",
        headers=cabecera(tokens["admin"]),
    ).json()
    assert filtradas["total"] == 1
    assert filtradas["items"][0]["paciente_rut"] == "44444444-4"


def test_descarga_de_archivo_inexistente_en_disco(cliente, tokens, almacen):
    subido = subir(cliente, tokens["admin"]).json()
    for archivo in almacen.iterdir():
        archivo.unlink()

    respuesta = cliente.get(
        f"/api/v1/documentos/{subido['id_documento']}/archivo",
        headers=cabecera(tokens["admin"]),
    )
    assert respuesta.status_code == 404
