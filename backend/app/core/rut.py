"""Normalizacion y validacion de RUT chileno (modulo 11)."""

import re

_PATRON_RUT = re.compile(r"^(\d{1,8})-([0-9K])$")


def calcular_digito_verificador(cuerpo: str) -> str:
    """Calcula el digito verificador de un cuerpo numerico de RUT."""
    suma = 0
    multiplicador = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1

    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def normalizar_rut(valor: str) -> str:
    """Devuelve el RUT en formato canonico: sin puntos, con guion y K mayuscula.

    Lanza ValueError si la estructura o el digito verificador no son validos.
    """
    if not isinstance(valor, str):
        raise ValueError("RUT invalido")

    limpio = re.sub(r"[.\s]", "", valor).upper()
    if "-" not in limpio:
        if len(limpio) < 2:
            raise ValueError("RUT invalido")
        limpio = f"{limpio[:-1]}-{limpio[-1]}"

    coincidencia = _PATRON_RUT.match(limpio)
    if coincidencia is None:
        raise ValueError("RUT invalido")

    cuerpo, digito = coincidencia.groups()
    if calcular_digito_verificador(cuerpo) != digito:
        raise ValueError("RUT invalido")

    return f"{cuerpo}-{digito}"


def es_rut_valido(valor: str) -> bool:
    try:
        normalizar_rut(valor)
    except ValueError:
        return False
    return True
