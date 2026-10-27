"""Modelo ORM de usuarios (cuentas que inician sesion)."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RolUsuario

FORMATO_RUT = "rut ~ '^[0-9]{1,8}-[0-9K]$'"


class Usuario(Base):
    __tablename__ = "usuarios"

    __table_args__ = (
        CheckConstraint(FORMATO_RUT, name="rut_formato"),
        CheckConstraint(
            "rol IN ('administrador', 'profesional')",
            name="rol_valido",
        ),
    )

    rut: Mapped[str] = mapped_column(String(12), primary_key=True)
    nombres: Mapped[str] = mapped_column(String(120), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(120), nullable=False)
    correo_electronico: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        Enum(
            RolUsuario,
            native_enum=False,
            create_constraint=False,
            length=20,
            values_callable=lambda enum: [miembro.value for miembro in enum],
            name="rol_usuario",
        ),
        nullable=False,
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
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    profesional: Mapped["Profesional | None"] = relationship(  # noqa: F821
        "Profesional",
        back_populates="usuario",
        uselist=False,
    )
