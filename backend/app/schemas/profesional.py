"""Esquemas de profesionales."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.rut import normalizar_rut


class ProfesionalCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    rut: str = Field(min_length=1, max_length=20)
    nombres: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=120)
    especialidad: str = Field(min_length=1, max_length=120)
    telefono: str = Field(min_length=1, max_length=30)
    correo_electronico: EmailStr
    usuario_rut: str | None = Field(default=None, max_length=20)
    activo: bool = True

    @field_validator("rut")
    @classmethod
    def _normalizar_rut(cls, valor: str) -> str:
        return normalizar_rut(valor)

    @field_validator("usuario_rut")
    @classmethod
    def _normalizar_usuario_rut(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        return normalizar_rut(valor)


class ProfesionalUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombres: str | None = Field(default=None, min_length=1, max_length=120)
    apellidos: str | None = Field(default=None, min_length=1, max_length=120)
    especialidad: str | None = Field(default=None, min_length=1, max_length=120)
    telefono: str | None = Field(default=None, min_length=1, max_length=30)
    correo_electronico: EmailStr | None = None
    usuario_rut: str | None = Field(default=None, max_length=20)
    activo: bool | None = None

    @field_validator("usuario_rut")
    @classmethod
    def _normalizar_usuario_rut(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        return normalizar_rut(valor)


class ProfesionalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rut: str
    nombres: str
    apellidos: str
    especialidad: str
    telefono: str
    correo_electronico: str
    usuario_rut: str | None
    activo: bool
    fecha_creacion: datetime
