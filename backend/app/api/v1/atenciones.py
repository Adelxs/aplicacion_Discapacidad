"""Endpoints de atenciones."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_actual, requiere_profesional
from app.db.session import get_db
from app.models import Usuario
from app.schemas.atencion import AtencionCreate, AtencionOut, AtencionUpdate
from app.schemas.common import Pagina
from app.services import atenciones as servicio

router = APIRouter(prefix="/atenciones", tags=["atenciones"])


@router.get("", response_model=Pagina[AtencionOut], summary="Listar atenciones")
def listar(
    paciente_rut: str | None = Query(
        default=None, description="Busqueda parcial por RUT del paciente"
    ),
    desde: date | None = Query(default=None, description="Desde (inclusive)"),
    hasta: date | None = Query(default=None, description="Hasta (inclusive)"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    return servicio.listar(
        db,
        usuario,
        paciente_rut=paciente_rut,
        desde=desde,
        hasta=hasta,
        pagina=page,
        por_pagina=per_page,
    )


@router.post(
    "",
    response_model=AtencionOut,
    status_code=201,
    summary="Registrar la atencion de una cita confirmada",
)
def crear(
    payload: AtencionCreate,
    usuario: Usuario = Depends(requiere_profesional),
    db: Session = Depends(get_db),
):
    return servicio.crear(db, payload, usuario)


@router.get(
    "/{id_atencion}", response_model=AtencionOut, summary="Obtener atencion"
)
def obtener(
    id_atencion: UUID,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    return servicio.obtener_visible(db, id_atencion, usuario)


@router.patch(
    "/{id_atencion}",
    response_model=AtencionOut,
    summary="Corregir el registro clinico",
)
def actualizar(
    id_atencion: UUID,
    payload: AtencionUpdate,
    usuario: Usuario = Depends(requiere_profesional),
    db: Session = Depends(get_db),
):
    return servicio.actualizar(db, id_atencion, payload, usuario)
