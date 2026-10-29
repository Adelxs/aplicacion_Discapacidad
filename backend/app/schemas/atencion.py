"""Esquemas de atenciones (registro clinico de una cita)."""

from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)

from app.core.tiempo import a_zona_local


class AtencionCreate(BaseModel):
    """Atencion de una cita confirmada.

    Paciente, profesional y autor se derivan de la cita y de la identidad
    autenticada; no se aceptan en el cuerpo.
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id_cita: UUID
    fecha_atencion: datetime
    motivo: str = Field(min_length=1, max_length=500)
    registro_clinico: str = Field(min_length=1, max_length=10000)

    @field_validator("fecha_atencion")
    @classmethod
    def _normalizar_fecha(cls, valor: datetime) -> datetime:
        return a_zona_local(valor)


class AtencionUpdate(BaseModel):
    """Correccion del registro por parte del profesional que la realizo."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    motivo: str | None = Field(default=None, min_length=1, max_length=500)
    registro_clinico: str | None = Field(
        default=None, min_length=1, max_length=10000
    )


class AtencionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_atencion: UUID
    id_cita: UUID
    paciente_rut: str
    profesional_rut: str
    fecha_atencion: datetime
    motivo: str
    registro_clinico: str
    creado_por_rut: str
    fecha_creacion: datetime

    @field_serializer("fecha_atencion", "fecha_creacion")
    def _presentar_en_zona_local(self, valor: datetime) -> datetime:
        return a_zona_local(valor)
