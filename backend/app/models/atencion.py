"""Modelo ORM de atenciones (registro clinico de una cita realizada)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Atencion(Base):
    __tablename__ = "atenciones"

    __table_args__ = (
        # Una cita puede tener como maximo una atencion.
        UniqueConstraint("id_cita", name="uq_atenciones_id_cita"),
        UniqueConstraint(
            "id_atencion",
            "paciente_rut",
            name="uq_atenciones_coherencia",
        ),
        # Paciente y profesional deben coincidir con los de la cita.
        ForeignKeyConstraint(
            ["id_cita", "paciente_rut", "profesional_rut"],
            [
                "citas.id_cita",
                "citas.paciente_rut",
                "citas.profesional_rut",
            ],
            name="fk_atenciones_cita_coherente",
            ondelete="RESTRICT",
        ),
        Index("ix_atenciones_paciente_rut", "paciente_rut"),
        Index("ix_atenciones_profesional_rut", "profesional_rut"),
    )

    id_atencion: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    id_cita: Mapped[uuid.UUID] = mapped_column(nullable=False)
    paciente_rut: Mapped[str] = mapped_column(
        String(12),
        ForeignKey(
            "pacientes.rut",
            name="fk_atenciones_paciente_rut_pacientes",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    profesional_rut: Mapped[str] = mapped_column(
        String(12),
        ForeignKey(
            "profesionales.rut",
            name="fk_atenciones_profesional_rut_profesionales",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    fecha_atencion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    registro_clinico: Mapped[str] = mapped_column(Text, nullable=False)
    creado_por_rut: Mapped[str] = mapped_column(
        String(12),
        ForeignKey(
            "usuarios.rut",
            name="fk_atenciones_creado_por_rut_usuarios",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    paciente: Mapped["Paciente"] = relationship(  # noqa: F821
        "Paciente",
        back_populates="atenciones",
        foreign_keys=[paciente_rut],
    )
    profesional: Mapped["Profesional"] = relationship(  # noqa: F821
        "Profesional",
        foreign_keys=[profesional_rut],
    )
    creado_por: Mapped["Usuario"] = relationship(  # noqa: F821
        "Usuario",
        foreign_keys=[creado_por_rut],
    )
