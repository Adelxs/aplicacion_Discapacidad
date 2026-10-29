"""Utilidades compartidas por los enrutadores."""

from app.core.errors import ErrorAPI
from app.core.rut import normalizar_rut


def rut_de_ruta(valor: str) -> str:
    """Normaliza un RUT recibido en la URL; si es invalido, responde 404."""
    try:
        return normalizar_rut(valor)
    except ValueError:
        raise ErrorAPI(
            status_code=404,
            mensaje="Recurso no encontrado.",
            codigo="no_encontrado",
        ) from None
