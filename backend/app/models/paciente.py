"""Modelo ORM de pacientes."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.usuario import FORMATO_RUT


class Paciente(Base):
    __tablename__ = "pacientes"

    __table_args__ = (
        CheckConstraint(FORMATO_RUT, name="rut_formato"),
        Index("ix_pacientes_apellidos_nombres", "apellidos", "nombres"),
    )

    rut: Mapped[str] = mapped_column(String(12), primary_key=True)
    nombres: Mapped[str] = mapped_column(String(120), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(120), nullable=False)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    correo_electronico: Mapped[str] = mapped_column(String(255), nullable=False)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
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

    citas: Mapped[list["Cita"]] = relationship(  # noqa: F821
        "Cita",
        back_populates="paciente",
    )
    atenciones: Mapped[list["Atencion"]] = relationship(  # noqa: F821
        "Atencion",
        back_populates="paciente",
    )
    documentos: Mapped[list["Documento"]] = relationship(  # noqa: F821
        "Documento",
        back_populates="paciente",
    )
