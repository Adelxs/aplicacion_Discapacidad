"""Manejo uniforme de errores de la API.

Todas las respuestas de error comparten la forma:

    {"error": {"codigo": "...", "mensaje": "...", "detalle": ...}}

Nunca se exponen trazas internas, consultas SQL ni datos privados.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_CODIGOS_POR_ESTADO = {
    400: "solicitud_invalida",
    401: "no_autenticado",
    403: "sin_permisos",
    404: "no_encontrado",
    405: "metodo_no_permitido",
    409: "conflicto",
    422: "datos_invalidos",
    500: "error_interno",
    503: "servicio_no_disponible",
}


class ErrorAPI(Exception):
    """Error de negocio controlado."""

    def __init__(
        self,
        status_code: int,
        mensaje: str,
        codigo: str | None = None,
        detalle: Any = None,
    ) -> None:
        self.status_code = status_code
        self.mensaje = mensaje
        self.codigo = codigo or _CODIGOS_POR_ESTADO.get(status_code, "error")
        self.detalle = detalle
        super().__init__(mensaje)


def _respuesta(
    status_code: int,
    codigo: str,
    mensaje: str,
    detalle: Any = None,
) -> JSONResponse:
    cuerpo: dict[str, Any] = {"codigo": codigo, "mensaje": mensaje}
    if detalle is not None:
        cuerpo["detalle"] = detalle
    return JSONResponse(status_code=status_code, content={"error": cuerpo})


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorAPI)
    async def _error_api(_: Request, exc: ErrorAPI) -> JSONResponse:
        return _respuesta(exc.status_code, exc.codigo, exc.mensaje, exc.detalle)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        codigo = _CODIGOS_POR_ESTADO.get(exc.status_code, "error")
        detalle = exc.detail if isinstance(exc.detail, str) else None
        mensaje = detalle or "La solicitud no pudo completarse."
        return _respuesta(exc.status_code, codigo, mensaje)

    @app.exception_handler(RequestValidationError)
    async def _validacion_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        campos = [
            {
                "campo": ".".join(str(parte) for parte in error.get("loc", ()) if parte != "body"),
                "mensaje": error.get("msg", "Valor invalido"),
            }
            for error in exc.errors()
        ]
        return _respuesta(
            422,
            "datos_invalidos",
            "Los datos enviados no son validos.",
            campos,
        )

    @app.exception_handler(Exception)
    async def _error_no_controlado(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Error no controlado en %s %s: %s",
            request.method,
            request.url.path,
            exc.__class__.__name__,
        )
        return _respuesta(
            500,
            "error_interno",
            "Ocurrio un error inesperado. Intente nuevamente.",
        )
