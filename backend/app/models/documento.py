"""Modelo ORM de documentos (metadatos de archivos privados)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Documento(Base):
    __tablename__ = "documentos"

    __table_args__ = (
        # Si el documento se asocia a una atencion, el paciente debe coincidir.
        # Al ser id_atencion nullable, PostgreSQL omite la comprobacion cuando
        # el documento no esta asociado a una atencion.
        ForeignKeyConstraint(
            ["id_atencion", "paciente_rut"],
            ["atenciones.id_atencion", "atenciones.paciente_rut"],
            name="fk_documentos_atencion_coherente",
            ondelete="RESTRICT",
        ),
        Index("ix_documentos_id_atencion", "id_atencion"),
    )

    id_documento: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    paciente_rut: Mapped[str] = mapped_column(
        String(12),
        ForeignKey(
            "pacientes.rut",
            name="fk_documentos_paciente_rut_pacientes",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    id_atencion: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    nombre_original: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_mime: Mapped[str] = mapped_column(String(120), nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    clave_archivo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    subido_por_rut: Mapped[str] = mapped_column(
        String(12),
        ForeignKey(
            "usuarios.rut",
            name="fk_documentos_subido_por_rut_usuarios",
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
        back_populates="documentos",
        foreign_keys=[paciente_rut],
    )
    subido_por: Mapped["Usuario"] = relationship(  # noqa: F821
        "Usuario",
        foreign_keys=[subido_por_rut],
    )
