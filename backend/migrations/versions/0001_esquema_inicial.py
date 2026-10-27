"""Esquema inicial del MVP.

Crea las seis entidades funcionales, sus relaciones, indices y restricciones,
incluida la proteccion contra solapamientos de agenda a nivel de base de datos.

Revision ID: 0001_esquema_inicial
Revises:
Create Date: 2026-10-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_esquema_inicial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FORMATO_RUT = "rut ~ '^[0-9]{1,8}-[0-9K]$'"
ESTADOS_CITA = (
    "estado IN ('pendiente', 'confirmada', 'atendida', 'cancelada', 'ausente')"
)


def upgrade() -> None:
    # Necesaria para la restriccion EXCLUDE que combina igualdad y rango.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.create_table(
        "usuarios",
        sa.Column("rut", sa.String(length=12), nullable=False),
        sa.Column("nombres", sa.String(length=120), nullable=False),
        sa.Column("apellidos", sa.String(length=120), nullable=False),
        sa.Column("correo_electronico", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column(
            "activo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(FORMATO_RUT, name="rut_formato"),
        sa.CheckConstraint(
            "rol IN ('administrador', 'profesional')",
            name="rol_valido",
        ),
        sa.PrimaryKeyConstraint("rut", name="pk_usuarios"),
    )

    op.create_table(
        "profesionales",
        sa.Column("rut", sa.String(length=12), nullable=False),
        sa.Column("nombres", sa.String(length=120), nullable=False),
        sa.Column("apellidos", sa.String(length=120), nullable=False),
        sa.Column("especialidad", sa.String(length=120), nullable=False),
        sa.Column("telefono", sa.String(length=30), nullable=False),
        sa.Column("correo_electronico", sa.String(length=255), nullable=False),
        sa.Column("usuario_rut", sa.String(length=12), nullable=True),
        sa.Column(
            "activo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(FORMATO_RUT, name="rut_formato"),
        sa.CheckConstraint(
            "usuario_rut IS NULL OR usuario_rut = rut",
            name="cuenta_mismo_rut",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_rut"],
            ["usuarios.rut"],
            name="fk_profesionales_usuario_rut_usuarios",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("rut", name="pk_profesionales"),
        sa.UniqueConstraint(
            "usuario_rut",
            name="uq_profesionales_usuario_rut",
        ),
    )

    op.create_table(
        "pacientes",
        sa.Column("rut", sa.String(length=12), nullable=False),
        sa.Column("nombres", sa.String(length=120), nullable=False),
        sa.Column("apellidos", sa.String(length=120), nullable=False),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=False),
        sa.Column("telefono", sa.String(length=30), nullable=False),
        sa.Column("correo_electronico", sa.String(length=255), nullable=False),
        sa.Column("direccion", sa.String(length=255), nullable=False),
        sa.Column(
            "activo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(FORMATO_RUT, name="rut_formato"),
        sa.PrimaryKeyConstraint("rut", name="pk_pacientes"),
    )

    op.create_table(
        "citas",
        sa.Column(
            "id_cita",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("paciente_rut", sa.String(length=12), nullable=False),
        sa.Column("profesional_rut", sa.String(length=12), nullable=False),
        sa.Column("fecha_hora_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_hora_fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column(
            "estado",
            sa.String(length=20),
            server_default=sa.text("'pendiente'"),
            nullable=False,
        ),
        sa.Column("observaciones_administrativas", sa.Text(), nullable=True),
        sa.Column("creado_por_rut", sa.String(length=12), nullable=False),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "fecha_hora_fin > fecha_hora_inicio",
            name="horario_valido",
        ),
        sa.CheckConstraint(ESTADOS_CITA, name="estado_valido"),
        sa.ForeignKeyConstraint(
            ["creado_por_rut"],
            ["usuarios.rut"],
            name="fk_citas_creado_por_rut_usuarios",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["paciente_rut"],
            ["pacientes.rut"],
            name="fk_citas_paciente_rut_pacientes",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["profesional_rut"],
            ["profesionales.rut"],
            name="fk_citas_profesional_rut_profesionales",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id_cita", name="pk_citas"),
        # Permite la clave foranea compuesta de atenciones.
        sa.UniqueConstraint(
            "id_cita",
            "paciente_rut",
            "profesional_rut",
            name="uq_citas_coherencia",
        ),
    )

    op.create_table(
        "atenciones",
        sa.Column(
            "id_atencion",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("id_cita", sa.Uuid(), nullable=False),
        sa.Column("paciente_rut", sa.String(length=12), nullable=False),
        sa.Column("profesional_rut", sa.String(length=12), nullable=False),
        sa.Column("fecha_atencion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("registro_clinico", sa.Text(), nullable=False),
        sa.Column("creado_por_rut", sa.String(length=12), nullable=False),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["id_cita", "paciente_rut", "profesional_rut"],
            [
                "citas.id_cita",
                "citas.paciente_rut",
                "citas.profesional_rut",
            ],
            name="fk_atenciones_cita_coherente",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["paciente_rut"],
            ["pacientes.rut"],
            name="fk_atenciones_paciente_rut_pacientes",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["profesional_rut"],
            ["profesionales.rut"],
            name="fk_atenciones_profesional_rut_profesionales",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["creado_por_rut"],
            ["usuarios.rut"],
            name="fk_atenciones_creado_por_rut_usuarios",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id_atencion", name="pk_atenciones"),
        sa.UniqueConstraint("id_cita", name="uq_atenciones_id_cita"),
        # Permite la clave foranea compuesta de documentos.
        sa.UniqueConstraint(
            "id_atencion",
            "paciente_rut",
            name="uq_atenciones_coherencia",
        ),
    )

    op.create_table(
        "documentos",
        sa.Column(
            "id_documento",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("paciente_rut", sa.String(length=12), nullable=False),
        sa.Column("id_atencion", sa.Uuid(), nullable=True),
        sa.Column("nombre_original", sa.String(length=255), nullable=False),
        sa.Column("tipo_mime", sa.String(length=120), nullable=False),
        sa.Column("tamano_bytes", sa.BigInteger(), nullable=False),
        sa.Column("clave_archivo", sa.String(length=255), nullable=False),
        sa.Column("subido_por_rut", sa.String(length=12), nullable=False),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["id_atencion", "paciente_rut"],
            ["atenciones.id_atencion", "atenciones.paciente_rut"],
            name="fk_documentos_atencion_coherente",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["paciente_rut"],
            ["pacientes.rut"],
            name="fk_documentos_paciente_rut_pacientes",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["subido_por_rut"],
            ["usuarios.rut"],
            name="fk_documentos_subido_por_rut_usuarios",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id_documento", name="pk_documentos"),
        sa.UniqueConstraint(
            "clave_archivo",
            name="uq_documentos_clave_archivo",
        ),
    )

    op.create_index(
        "ix_pacientes_apellidos_nombres",
        "pacientes",
        ["apellidos", "nombres"],
    )
    op.create_index(
        "ix_profesionales_apellidos_nombres",
        "profesionales",
        ["apellidos", "nombres"],
    )
    op.create_index(
        "ix_citas_profesional_fecha",
        "citas",
        ["profesional_rut", "fecha_hora_inicio"],
    )
    op.create_index("ix_citas_paciente_rut", "citas", ["paciente_rut"])
    op.create_index("ix_citas_estado", "citas", ["estado"])
    op.create_index("ix_atenciones_paciente_rut", "atenciones", ["paciente_rut"])
    op.create_index(
        "ix_atenciones_profesional_rut",
        "atenciones",
        ["profesional_rut"],
    )
    op.create_index("ix_documentos_paciente_rut", "documentos", ["paciente_rut"])
    op.create_index("ix_documentos_id_atencion", "documentos", ["id_atencion"])

    # Solapamientos: la base de datos garantiza la regla incluso con
    # solicitudes concurrentes. Las citas canceladas liberan el horario.
    op.execute(
        """
        ALTER TABLE citas
        ADD CONSTRAINT ex_citas_profesional_horario
        EXCLUDE USING gist (
            profesional_rut WITH =,
            tstzrange(fecha_hora_inicio, fecha_hora_fin, '[)') WITH &&
        )
        WHERE (estado <> 'cancelada')
        """
    )


def downgrade() -> None:
    op.drop_table("documentos")
    op.drop_table("atenciones")
    op.drop_table("citas")
    op.drop_table("pacientes")
    op.drop_table("profesionales")
    op.drop_table("usuarios")
