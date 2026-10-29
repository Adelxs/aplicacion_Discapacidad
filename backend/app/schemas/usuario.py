"""Esquemas de usuarios."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.rut import normalizar_rut
from app.models import RolUsuario


class UsuarioCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    rut: str = Field(min_length=1, max_length=20)
    nombres: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=120)
    correo_electronico: EmailStr
    password: str = Field(min_length=8, max_length=128)
    rol: RolUsuario
    activo: bool = True

    @field_validator("rut")
    @classmethod
    def _normalizar_rut(cls, valor: str) -> str:
        return normalizar_rut(valor)


class UsuarioUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombres: str | None = Field(default=None, min_length=1, max_length=120)
    apellidos: str | None = Field(default=None, min_length=1, max_length=120)
    correo_electronico: EmailStr | None = None
    rol: RolUsuario | None = None
    activo: bool | None = None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rut: str
    nombres: str
    apellidos: str
    correo_electronico: str
    rol: RolUsuario
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime
