"""Pruebas de integridad del esquema (Etapa 2).

Verifican claves foraneas, restricciones CHECK, unicidad y la proteccion
contra solapamientos de agenda. Usan datos sinteticos, nunca datos reales.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

BASE = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)


def m(valor: int) -> datetime:
    return BASE + timedelta(minutes=valor)


def insertar_documento(
    conexion,
    *,
    paciente: str,
    id_atencion=None,
    clave: str = "archivo-sintetico-001",
):
    return conexion.execute(
        text(
            """
            INSERT INTO documentos
                (paciente_rut, id_atencion, nombre_original, tipo_mime,
                 tamano_bytes, clave_archivo, subido_por_rut)
            VALUES
                (:paciente, :atencion, 'informe.pdf', 'application/pdf',
                 1024, :clave, '22222222-2')
            RETURNING id_documento
            """
        ),
        {"paciente": paciente, "atencion": id_atencion, "clave": clave},
    ).scalar_one()


def test_tablas_del_esquema(motor_pruebas):
    tablas = set(inspect(motor_pruebas).get_table_names())
    esperadas = {
        "usuarios",
        "profesionales",
        "pacientes",
        "citas",
        "atenciones",
        "documentos",
    }
    assert esperadas <= tablas


def test_restriccion_de_exclusion_registrada(conexion):
    nombre = conexion.execute(
        text(
            "SELECT conname FROM pg_constraint "
            "WHERE conname = 'ex_citas_profesional_horario'"
        )
    ).scalar()
    assert nombre == "ex_citas_profesional_horario"


def test_fechas_almacenadas_con_zona_horaria(conexion):
    tipo = conexion.execute(
        text(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'citas'
              AND column_name = 'fecha_hora_inicio'
            """
        )
    ).scalar()
    assert tipo == "timestamp with time zone"


def test_activo_tiene_valor_por_defecto(datos_base):
    activo = datos_base.execute(
        text("SELECT activo FROM usuarios WHERE rut = '11111111-1'")
    ).scalar()
    assert activo is True


def test_rut_con_formato_no_canonico_es_rechazado(conexion):
    with pytest.raises(IntegrityError, match="ck_usuarios_rut_formato"):
        conexion.execute(
            text(
                """
                INSERT INTO usuarios
                    (rut, nombres, apellidos, correo_electronico,
                     password_hash, rol)
                VALUES
                    ('12.345.678-5', 'Rut', 'Invalido',
                     'invalido@ejemplo.test', 'hash-de-prueba', 'profesional')
                """
            )
        )


def test_horario_con_fin_anterior_al_inicio_es_rechazado(
    datos_base, crear_cita
):
    with pytest.raises(IntegrityError, match="ck_citas_horario_valido"):
        crear_cita(inicio=m(60), fin=m(30))


def test_solapamiento_es_rechazado(datos_base, crear_cita):
    crear_cita(inicio=m(0), fin=m(60))
    with pytest.raises(IntegrityError, match="ex_citas_profesional_horario"):
        crear_cita(inicio=m(30), fin=m(90))


def test_citas_contiguas_son_permitidas(datos_base, crear_cita):
    crear_cita(inicio=m(0), fin=m(30))
    crear_cita(inicio=m(30), fin=m(60))


def test_cita_cancelada_no_bloquea_el_horario(datos_base, crear_cita):
    crear_cita(inicio=m(0), fin=m(60), estado="cancelada")
    crear_cita(inicio=m(0), fin=m(60), estado="pendiente")


def test_dos_profesionales_pueden_compartir_horario(datos_base, crear_cita):
    crear_cita(profesional="22222222-2", inicio=m(0), fin=m(60))
    crear_cita(profesional="55555555-5", inicio=m(0), fin=m(60))


def test_estado_de_cita_invalido_es_rechazado(datos_base, crear_cita):
    with pytest.raises(IntegrityError, match="ck_citas_estado_valido"):
        crear_cita(estado="reprogramada")


def test_una_sola_atencion_por_cita(datos_base, crear_cita, crear_atencion):
    cita = crear_cita()
    crear_atencion(id_cita=cita)
    with pytest.raises(IntegrityError, match="uq_atenciones_id_cita"):
        crear_atencion(id_cita=cita)


def test_atencion_con_paciente_distinto_al_de_la_cita_es_rechazada(
    datos_base, crear_cita, crear_atencion
):
    cita = crear_cita(paciente="33333333-3")
    with pytest.raises(IntegrityError, match="fk_atenciones_cita_coherente"):
        crear_atencion(id_cita=cita, paciente="44444444-4")


def test_atencion_coherente_se_registra(datos_base, crear_cita, crear_atencion):
    cita = crear_cita(paciente="33333333-3", profesional="22222222-2")
    atencion = crear_atencion(
        id_cita=cita, paciente="33333333-3", profesional="22222222-2"
    )
    assert atencion is not None


def test_documento_con_paciente_distinto_al_de_la_atencion_es_rechazado(
    datos_base, crear_cita, crear_atencion
):
    cita = crear_cita(paciente="33333333-3")
    atencion = crear_atencion(id_cita=cita, paciente="33333333-3")

    with pytest.raises(
        IntegrityError, match="fk_documentos_atencion_coherente"
    ):
        insertar_documento(
            datos_base,
            paciente="44444444-4",
            id_atencion=atencion,
        )


def test_documento_sin_atencion_es_permitido(datos_base):
    documento = insertar_documento(
        datos_base,
        paciente="33333333-3",
        id_atencion=None,
    )
    assert documento is not None


def test_clave_de_archivo_es_unica(datos_base):
    insertar_documento(datos_base, paciente="33333333-3", clave="unica-001")
    with pytest.raises(IntegrityError, match="uq_documentos_clave_archivo"):
        insertar_documento(datos_base, paciente="44444444-4", clave="unica-001")


def test_paciente_con_historial_no_puede_eliminarse(
    datos_base, crear_cita
):
    crear_cita(paciente="33333333-3")
    with pytest.raises(
        IntegrityError, match="fk_citas_paciente_rut_pacientes"
    ):
        datos_base.execute(
            text("DELETE FROM pacientes WHERE rut = '33333333-3'")
        )


def test_profesional_con_cuenta_asociada_debe_compartir_rut(datos_base):
    with pytest.raises(
        IntegrityError, match="ck_profesionales_cuenta_mismo_rut"
    ):
        datos_base.execute(
            text(
                """
                INSERT INTO profesionales
                    (rut, nombres, apellidos, especialidad, telefono,
                     correo_electronico, usuario_rut)
                VALUES
                    ('55555555-5', 'Rita', 'Profesional', 'Kinesiologia',
                     '+56900000005', 'rita@ejemplo.test', '11111111-1')
                """
            )
        )
