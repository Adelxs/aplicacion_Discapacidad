"""Dependencias de autenticacion y autorizacion."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import ErrorAPI
from app.core.security import TokenInvalidoError, decodificar_token
from app.db.session import get_db
from app.models import RolUsuario, Usuario

portador = HTTPBearer(
    auto_error=False,
    description="Token JWT obtenido en /api/v1/auth/login",
)


def _no_autenticado() -> ErrorAPI:
    return ErrorAPI(
        status_code=401,
        mensaje="No se pudo validar la sesion. Inicie sesion nuevamente.",
        codigo="no_autenticado",
    )


def get_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(portador),
    db: Session = Depends(get_db),
) -> Usuario:
    """Identifica al usuario autenticado a partir del token Bearer."""
    if credenciales is None or credenciales.scheme.lower() != "bearer":
        raise _no_autenticado()

    try:
        datos = decodificar_token(credenciales.credentials)
    except TokenInvalidoError:
        raise _no_autenticado() from None

    rut = datos.get("sub")
    usuario = db.get(Usuario, rut) if isinstance(rut, str) else None

    # Una cuenta desactivada pierde acceso de inmediato, aunque su token
    # siga vigente.
    if usuario is None or not usuario.activo:
        raise _no_autenticado()

    return usuario


def requiere_roles(*roles: RolUsuario):
    """Dependencia que exige uno de los roles indicados."""

    def _verificar(
        usuario: Usuario = Depends(get_usuario_actual),
    ) -> Usuario:
        if usuario.rol not in roles:
            raise ErrorAPI(
                status_code=403,
                mensaje="No tiene permisos para realizar esta accion.",
                codigo="sin_permisos",
            )
        return usuario

    return _verificar


requiere_administrador = requiere_roles(RolUsuario.ADMINISTRADOR)
requiere_profesional = requiere_roles(RolUsuario.PROFESIONAL)
