"""Modelo ORM de profesionales del centro."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.usuario import FORMATO_RUT


class Profesional(Base):
    __tablename__ = "profesionales"

    __table_args__ = (
        CheckConstraint(FORMATO_RUT, name="rut_formato"),
        # Cuando existe una cuenta vinculada, ambos RUT deben ser el mismo.
        CheckConstraint(
            "usuario_rut IS NULL OR usuario_rut = rut",
            name="cuenta_mismo_rut",
        ),
        UniqueConstraint(  # Una cuenta como maximo por profesional.
            "usuario_rut",
            name="uq_profesionales_usuario_rut",
        ),
        Index("ix_profesionales_apellidos_nombres", "apellidos", "nombres"),
    )

    rut: Mapped[str] = mapped_column(String(12), primary_key=True)
    nombres: Mapped[str] = mapped_column(String(120), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(120), nullable=False)
    especialidad: Mapped[str] = mapped_column(String(120), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    correo_electronico: Mapped[str] = mapped_column(String(255), nullable=False)
    usuario_rut: Mapped[str | None] = mapped_column(
        String(12),
        ForeignKey(
            "usuarios.rut",
            name="fk_profesionales_usuario_rut_usuarios",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
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

    usuario: Mapped["Usuario | None"] = relationship(  # noqa: F821
        "Usuario",
        back_populates="profesional",
    )
