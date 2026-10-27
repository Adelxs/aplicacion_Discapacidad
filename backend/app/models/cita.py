"""Modelo ORM de citas (agenda profesional)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EstadoCita

ESTADOS_VALIDOS_SQL = (
    "estado IN ('pendiente', 'confirmada', 'atendida', 'cancelada', 'ausente')"
)


class Cita(Base):
    __tablename__ = "citas"

    __table_args__ = (
        CheckConstraint(
            "fecha_hora_fin > fecha_hora_inicio",
            name="horario_valido",
        ),
        CheckConstraint(ESTADOS_VALIDOS_SQL, name="estado_valido"),
        # Permite que atenciones referencie la tripla completa de la cita.
        UniqueConstraint(
            "id_cita",
            "paciente_rut",
            "profesional_rut",
            name="uq_citas_coherencia",
        ),
        Index("ix_citas_profesional_fecha", "profesional_rut", "fecha_hora_inicio"),
        Index("ix_citas_paciente_rut", "paciente_rut"),
        Index("ix_citas_estado", "estado"),
        # Solapamientos seguros ante concurrencia. Las citas canceladas
        # no bloquean el horario.
        ExcludeConstraint(
            (text("profesional_rut"), "="),
            (
                text("tstzrange(fecha_hora_inicio, fecha_hora_fin, '[)')"),
                "&&",
            ),
            using="gist",
            where=text("estado <> 'cancelada'"),
            name="ex_citas_profesional_horario",
        ),
    )

    id_cita: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    paciente_rut: Mapped[str] = mapped_column(
        String(12),
        ForeignKey(
            "pacientes.rut",
            name="fk_citas_paciente_rut_pacientes",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    profesional_rut: Mapped[str] = mapped_column(
        String(12),
        ForeignKey(
            "profesionales.rut",
            name="fk_citas_profesional_rut_profesionales",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    fecha_hora_inicio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    fecha_hora_fin: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[EstadoCita] = mapped_column(
        Enum(
            EstadoCita,
            native_enum=False,
            create_constraint=False,
            length=20,
            values_callable=lambda enum: [miembro.value for miembro in enum],
            name="estado_cita",
        ),
        nullable=False,
        server_default=text("'pendiente'"),
    )
    observaciones_administrativas: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    creado_por_rut: Mapped[str] = mapped_column(
        String(12),
        ForeignKey(
            "usuarios.rut",
            name="fk_citas_creado_por_rut_usuarios",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    paciente: Mapped["Paciente"] = relationship(  # noqa: F821
        "Paciente",
        back_populates="citas",
    )
    profesional: Mapped["Profesional"] = relationship("Profesional")  # noqa: F821
    creado_por: Mapped["Usuario"] = relationship("Usuario")  # noqa: F821
