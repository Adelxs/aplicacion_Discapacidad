"""Esquemas de documentos."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

from app.core.tiempo import a_zona_local


class DocumentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_documento: UUID
    paciente_rut: str
    id_atencion: UUID | None
    nombre_original: str
    tipo_mime: str
    tamano_bytes: int
    subido_por_rut: str
    fecha_creacion: datetime

    @field_serializer("fecha_creacion")
    def _presentar_en_zona_local(self, valor: datetime) -> datetime:
        return a_zona_local(valor)
