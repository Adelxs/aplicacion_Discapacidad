"""Esquemas de autenticacion."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import RolUsuario


class LoginRequest(BaseModel):
    rut: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=1, max_length=128)


class UsuarioAutenticado(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rut: str
    nombres: str
    apellidos: str
    rol: RolUsuario


class UsuarioActual(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rut: str
    nombres: str
    apellidos: str
    correo_electronico: str
    rol: RolUsuario
    activo: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    usuario: UsuarioAutenticado
