"""Utilidades de fecha y hora en la zona horaria local del sistema."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

ZONA_HORARIA = ZoneInfo("America/Santiago")


def a_zona_local(valor: datetime) -> datetime:
    """Interpreta un datetime sin zona como hora de Santiago y normaliza el resto.

    Almacenamiento y presentacion usan `America/Santiago`, tal como exige la
    especificacion. Un instante con offset explicito se respeta y solo se
    convierte de zona para mostrarlo.
    """
    if valor.tzinfo is None:
        return valor.replace(tzinfo=ZONA_HORARIA)
    return valor.astimezone(ZONA_HORARIA)


def inicio_del_dia(valor: date) -> datetime:
    """Medianoche de `valor` en la zona horaria local."""
    return datetime.combine(valor, datetime.min.time(), tzinfo=ZONA_HORARIA)
