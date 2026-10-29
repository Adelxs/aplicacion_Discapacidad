"""Esquemas de citas y agenda."""

from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from app.core.rut import normalizar_rut
from app.core.tiempo import a_zona_local
from app.models import EstadoCita


class CitaCreate(BaseModel):
    """Cita solicitada por el profesional autenticado.

    El profesional, el estado inicial y el autor se determinan en el servidor:
    no se aceptan en el cuerpo de la solicitud.
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    paciente_rut: str = Field(min_length=1, max_length=20)
    fecha_hora_inicio: datetime
    fecha_hora_fin: datetime
    motivo: str = Field(min_length=1, max_length=500)

    @field_validator("paciente_rut")
    @classmethod
    def _normalizar_rut(cls, valor: str) -> str:
        return normalizar_rut(valor)

    @field_validator("fecha_hora_inicio", "fecha_hora_fin")
    @classmethod
    def _normalizar_horario(cls, valor: datetime) -> datetime:
        return a_zona_local(valor)

    @model_validator(mode="after")
    def _horario_valido(self) -> "CitaCreate":
        if self.fecha_hora_fin <= self.fecha_hora_inicio:
            raise ValueError(
                "La fecha y hora de fin debe ser posterior a la de inicio."
            )
        return self


class CitaObservacionesUpdate(BaseModel):
    """Unico campo que el administrador puede modificar de una cita."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    observaciones_administrativas: str | None = Field(
        default=None, max_length=1000
    )


class CitaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_cita: UUID
    paciente_rut: str
    profesional_rut: str
    fecha_hora_inicio: datetime
    fecha_hora_fin: datetime
    motivo: str
    estado: EstadoCita
    observaciones_administrativas: str | None
    creado_por_rut: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    @field_serializer(
        "fecha_hora_inicio",
        "fecha_hora_fin",
        "fecha_creacion",
        "fecha_actualizacion",
    )
    def _presentar_en_zona_local(self, valor: datetime) -> datetime:
        return a_zona_local(valor)
