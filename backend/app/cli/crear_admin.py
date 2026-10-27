"""Crea la cuenta administradora inicial (arranque del sistema).

Uso:
    docker compose exec backend python -m app.cli.crear_admin \
        --rut 12345678-9 --nombres Ana --apellidos Perez \
        --correo ana@ejemplo.cl

La contrasena se solicita de forma interactiva para no dejarla en el
historial de comandos ni en los logs.
"""

import argparse
import getpass
import sys

from app.core.config import settings
from app.core.rut import normalizar_rut
from app.core.security import hashear_password
from app.db.session import SessionLocal
from app.models import RolUsuario, Usuario


def _solicitar_password() -> str:
    password = getpass.getpass("Contrasena: ")
    confirmacion = getpass.getpass("Repetir contrasena: ")
    if password != confirmacion:
        raise SystemExit("Las contrasenas no coinciden.")
    if len(password) < settings.password_min_length:
        raise SystemExit(
            f"La contrasena debe tener al menos {settings.password_min_length} caracteres."
        )
    return password


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Crea la cuenta administradora inicial."
    )
    parser.add_argument("--rut", required=True)
    parser.add_argument("--nombres", required=True)
    parser.add_argument("--apellidos", required=True)
    parser.add_argument("--correo", required=True)
    argumentos = parser.parse_args(argv)

    try:
        rut = normalizar_rut(argumentos.rut)
    except ValueError:
        print("RUT invalido.", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        if db.get(Usuario, rut) is not None:
            print(f"Ya existe un usuario con RUT {rut}.", file=sys.stderr)
            return 1

        usuario = Usuario(
            rut=rut,
            nombres=argumentos.nombres.strip(),
            apellidos=argumentos.apellidos.strip(),
            correo_electronico=argumentos.correo.strip(),
            password_hash=hashear_password(_solicitar_password()),
            rol=RolUsuario.ADMINISTRADOR,
            activo=True,
        )
        db.add(usuario)
        db.commit()

    print(f"Cuenta administradora creada: {rut}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
