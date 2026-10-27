"""Endpoints de autenticacion."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_actual
from app.core.errors import ErrorAPI
from app.core.rut import normalizar_rut
from app.core.security import (
    crear_token_acceso,
    verificar_password,
    verificar_password_ficticio,
)
from app.db.session import get_db
from app.models import Usuario
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UsuarioActual,
    UsuarioAutenticado,
)

router = APIRouter(prefix="/auth", tags=["autenticacion"])


def _credenciales_invalidas() -> ErrorAPI:
    # Mismo mensaje para RUT inexistente, contrasena incorrecta o cuenta
    # desactivada: no se revela si la cuenta existe.
    return ErrorAPI(
        status_code=401,
        mensaje="RUT o contrasena incorrectos.",
        codigo="credenciales_invalidas",
    )


@router.post("/login", response_model=LoginResponse, summary="Iniciar sesion")
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    try:
        rut = normalizar_rut(payload.rut)
    except ValueError:
        raise _credenciales_invalidas() from None

    usuario = db.get(Usuario, rut)
    if usuario is None:
        verificar_password_ficticio(payload.password)
        raise _credenciales_invalidas()

    if not verificar_password(payload.password, usuario.password_hash):
        raise _credenciales_invalidas()

    if not usuario.activo:
        raise _credenciales_invalidas()

    token, segundos = crear_token_acceso(rut=usuario.rut, rol=usuario.rol.value)
    return LoginResponse(
        access_token=token,
        expires_in=segundos,
        usuario=UsuarioAutenticado.model_validate(usuario),
    )


@router.get("/me", response_model=UsuarioActual, summary="Identidad actual")
def me(usuario: Usuario = Depends(get_usuario_actual)) -> UsuarioActual:
    return UsuarioActual.model_validate(usuario)
