"""Fixtures de pruebas.

Las pruebas de integracion usan una base de datos separada de desarrollo,
creada y eliminada por la propia sesion de pytest. Nunca se usan datos reales.
"""

import os
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import Connection, make_url

from app.core.config import settings

NOMBRE_BD_PRUEBAS = os.getenv("TEST_DATABASE_NAME", "citas_municipales_test")

INICIO_BASE = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)


def minutos(valor: int) -> datetime:
    return INICIO_BASE + timedelta(minutes=valor)


@pytest.fixture(scope="session")
def motor_pruebas() -> Iterator[Engine]:
    url_pruebas = make_url(settings.database_url).set(database=NOMBRE_BD_PRUEBAS)
    url_admin = make_url(settings.database_url).set(database="postgres")

    motor_admin = create_engine(url_admin, isolation_level="AUTOCOMMIT")
    with motor_admin.connect() as conexion:
        existe = conexion.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :nombre"),
            {"nombre": NOMBRE_BD_PRUEBAS},
        ).scalar()
        if not existe:
            conexion.execute(text(f'CREATE DATABASE "{NOMBRE_BD_PRUEBAS}"'))

    anterior = os.environ.get("ALEMBIC_DATABASE_URL")
    os.environ["ALEMBIC_DATABASE_URL"] = url_pruebas.render_as_string(
        hide_password=False
    )
    try:
        command.upgrade(Config("alembic.ini"), "head")
    finally:
        if anterior is None:
            os.environ.pop("ALEMBIC_DATABASE_URL", None)
        else:
            os.environ["ALEMBIC_DATABASE_URL"] = anterior

    motor = create_engine(url_pruebas)
    try:
        yield motor
    finally:
        motor.dispose()
        with motor_admin.connect() as conexion:
            conexion.execute(
                text(f'DROP DATABASE IF EXISTS "{NOMBRE_BD_PRUEBAS}" WITH (FORCE)')
            )
        motor_admin.dispose()


@pytest.fixture()
def conexion(motor_pruebas: Engine) -> Iterator[Connection]:
    with motor_pruebas.connect() as conexion:
        transaccion = conexion.begin()
        try:
            yield conexion
        finally:
            transaccion.rollback()


@pytest.fixture()
def datos_base(conexion: Connection) -> Connection:
    conexion.execute(
        text(
            """
            INSERT INTO usuarios
                (rut, nombres, apellidos, correo_electronico, password_hash, rol)
            VALUES
                ('11111111-1', 'Ana', 'Administradora',
                 'ana@ejemplo.test', 'hash-de-prueba', 'administrador'),
                ('22222222-2', 'Pablo', 'Profesional',
                 'pablo@ejemplo.test', 'hash-de-prueba', 'profesional')
            """
        )
    )
    conexion.execute(
        text(
            """
            INSERT INTO profesionales
                (rut, nombres, apellidos, especialidad, telefono,
                 correo_electronico, usuario_rut)
            VALUES
                ('22222222-2', 'Pablo', 'Profesional', 'Psicologia',
                 '+56900000002', 'pablo@ejemplo.test', '22222222-2'),
                ('55555555-5', 'Rita', 'Profesional', 'Kinesiologia',
                 '+56900000005', 'rita@ejemplo.test', NULL)
            """
        )
    )
    conexion.execute(
        text(
            """
            INSERT INTO pacientes
                (rut, nombres, apellidos, fecha_nacimiento, telefono,
                 correo_electronico, direccion)
            VALUES
                ('33333333-3', 'Paula', 'Paciente', '1990-05-10',
                 '+56900000003', 'paula@ejemplo.test', 'Calle Falsa 123'),
                ('44444444-4', 'Pedro', 'Paciente', '1985-02-20',
                 '+56900000004', 'pedro@ejemplo.test', 'Calle Falsa 456')
            """
        )
    )
    return conexion


@pytest.fixture()
def crear_cita(datos_base: Connection):
    def _crear(
        *,
        paciente: str = "33333333-3",
        profesional: str = "22222222-2",
        inicio: datetime | None = None,
        fin: datetime | None = None,
        estado: str = "pendiente",
        motivo: str = "Consulta de prueba",
    ):
        return datos_base.execute(
            text(
                """
                INSERT INTO citas
                    (paciente_rut, profesional_rut, fecha_hora_inicio,
                     fecha_hora_fin, motivo, estado, creado_por_rut)
                VALUES
                    (:paciente, :profesional, :inicio, :fin, :motivo,
                     :estado, :creado_por)
                RETURNING id_cita
                """
            ),
            {
                "paciente": paciente,
                "profesional": profesional,
                "inicio": inicio or minutos(0),
                "fin": fin or minutos(60),
                "motivo": motivo,
                "estado": estado,
                "creado_por": "22222222-2",
            },
        ).scalar_one()

    return _crear


@pytest.fixture()
def crear_atencion(datos_base: Connection):
    def _crear(
        *,
        id_cita,
        paciente: str = "33333333-3",
        profesional: str = "22222222-2",
    ):
        return datos_base.execute(
            text(
                """
                INSERT INTO atenciones
                    (id_cita, paciente_rut, profesional_rut, fecha_atencion,
                     motivo, registro_clinico, creado_por_rut)
                VALUES
                    (:id_cita, :paciente, :profesional, :fecha, :motivo,
                     :registro, :creado_por)
                RETURNING id_atencion
                """
            ),
            {
                "id_cita": id_cita,
                "paciente": paciente,
                "profesional": profesional,
                "fecha": minutos(30),
                "motivo": "Atencion de prueba",
                "registro": "Registro clinico sintetico, sin datos reales.",
                "creado_por": profesional,
            },
        ).scalar_one()

    return _crear
