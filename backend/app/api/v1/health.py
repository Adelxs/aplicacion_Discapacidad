"""Comprobaciones de salud del servicio y de la base de datos."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ErrorAPI
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["salud"])


@router.get("/health", summary="Estado del servicio")
def estado_servicio() -> dict:
    ahora = datetime.now(ZoneInfo(settings.zona_horaria))
    return {
        "estado": "ok",
        "servicio": settings.app_name,
        "version": settings.app_version,
        "entorno": settings.entorno,
        "zona_horaria": settings.zona_horaria,
        "fecha_hora": ahora.isoformat(timespec="seconds"),
    }


@router.get("/health/db", summary="Estado de la base de datos")
def estado_base_de_datos(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.error("Fallo de conexion a la base de datos: %s", exc.__class__.__name__)
        raise ErrorAPI(
            status_code=503,
            mensaje="La base de datos no se encuentra disponible.",
            codigo="base_de_datos_no_disponible",
        ) from exc

    return {
        "estado": "ok",
        "base_de_datos": "disponible",
        "motor": "postgresql",
    }
