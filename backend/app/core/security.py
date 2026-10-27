"""Hash de contrasenas y emision/validacion de tokens JWT."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

# Argon2id con parametros explicitos para que el costo no dependa del entorno.
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


class TokenInvalidoError(Exception):
    """El token no tiene firma valida, esta expirado o le faltan datos."""


def hashear_password(password: str) -> str:
    return _hasher.hash(password)


def verificar_password(password: str, hash_guardado: str) -> bool:
    try:
        return _hasher.verify(hash_guardado, password)
    except (VerificationError, InvalidHashError):
        return False


# Se usa cuando el RUT no existe para que el tiempo de respuesta no delate
# si la cuenta esta registrada.
_HASH_FICTICIO = _hasher.hash("verificacion-de-tiempo-constante")


def verificar_password_ficticio(password: str) -> None:
    verificar_password(password, _HASH_FICTICIO)


def crear_token_acceso(
    rut: str,
    rol: str,
    expira_en_minutos: int | None = None,
) -> tuple[str, int]:
    """Devuelve (token, segundos_de_vigencia)."""
    minutos = (
        expira_en_minutos
        if expira_en_minutos is not None
        else settings.access_token_expire_minutes
    )
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": rut,
        "rol": rol,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=minutos),
    }
    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, minutos * 60


def decodificar_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.InvalidTokenError as exc:
        raise TokenInvalidoError("Token invalido") from exc
