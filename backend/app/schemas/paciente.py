"""Esquemas de pacientes."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.rut import normalizar_rut


class PacienteCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    rut: str = Field(min_length=1, max_length=20)
    nombres: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=120)
    fecha_nacimiento: date
    telefono: str = Field(min_length=1, max_length=30)
    correo_electronico: EmailStr
    direccion: str = Field(min_length=1, max_length=255)
    activo: bool = True

    @field_validator("rut")
    @classmethod
    def _normalizar_rut(cls, valor: str) -> str:
        return normalizar_rut(valor)

    @field_validator("fecha_nacimiento")
    @classmethod
    def _fecha_no_futura(cls, valor: date) -> date:
        if valor > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura.")
        return valor


class PacienteUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombres: str | None = Field(default=None, min_length=1, max_length=120)
    apellidos: str | None = Field(default=None, min_length=1, max_length=120)
    fecha_nacimiento: date | None = None
    telefono: str | None = Field(default=None, min_length=1, max_length=30)
    correo_electronico: EmailStr | None = None
    direccion: str | None = Field(default=None, min_length=1, max_length=255)
    activo: bool | None = None

    @field_validator("fecha_nacimiento")
    @classmethod
    def _fecha_no_futura(cls, valor: date | None) -> date | None:
        if valor is not None and valor > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura.")
        return valor


class PacienteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rut: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    telefono: str
    correo_electronico: str
    direccion: str
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime
