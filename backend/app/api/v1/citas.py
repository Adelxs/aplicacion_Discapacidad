"""Endpoints de citas y agenda."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import (
    get_usuario_actual,
    requiere_administrador,
    requiere_profesional,
)
from app.db.session import get_db
from app.models import EstadoCita, Usuario
from app.schemas.cita import CitaCreate, CitaObservacionesUpdate, CitaOut
from app.schemas.common import Pagina
from app.services import citas as servicio

router = APIRouter(prefix="/citas", tags=["citas"])


@router.get("", response_model=Pagina[CitaOut], summary="Listar citas")
def listar(
    paciente_rut: str | None = Query(
        default=None, description="Busqueda parcial por RUT del paciente"
    ),
    estado: EstadoCita | None = None,
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
        estado=estado,
        desde=desde,
        hasta=hasta,
        pagina=page,
        por_pagina=per_page,
    )


@router.post(
    "",
    response_model=CitaOut,
    status_code=201,
    summary="Agendar cita para el profesional autenticado",
)
def crear(
    payload: CitaCreate,
    usuario: Usuario = Depends(requiere_profesional),
    db: Session = Depends(get_db),
):
    return servicio.crear(db, payload, usuario)


@router.get("/{id_cita}", response_model=CitaOut, summary="Obtener cita")
def obtener(
    id_cita: UUID,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    return servicio.obtener_visible(db, id_cita, usuario)


@router.post(
    "/{id_cita}/confirmar",
    response_model=CitaOut,
    summary="Confirmar cita",
)
def confirmar(
    id_cita: UUID,
    usuario: Usuario = Depends(requiere_profesional),
    db: Session = Depends(get_db),
):
    return servicio.cambiar_estado(db, id_cita, usuario, EstadoCita.CONFIRMADA)


@router.post(
    "/{id_cita}/cancelar",
    response_model=CitaOut,
    summary="Cancelar cita",
)
def cancelar(
    id_cita: UUID,
    usuario: Usuario = Depends(requiere_profesional),
    db: Session = Depends(get_db),
):
    return servicio.cambiar_estado(db, id_cita, usuario, EstadoCita.CANCELADA)


@router.post(
    "/{id_cita}/ausente",
    response_model=CitaOut,
    summary="Marcar al paciente como ausente",
)
def marcar_ausente(
    id_cita: UUID,
    usuario: Usuario = Depends(requiere_profesional),
    db: Session = Depends(get_db),
):
    return servicio.cambiar_estado(db, id_cita, usuario, EstadoCita.AUSENTE)


@router.patch(
    "/{id_cita}/observaciones",
    response_model=CitaOut,
    summary="Registrar observaciones administrativas",
    dependencies=[Depends(requiere_administrador)],
)
def actualizar_observaciones(
    id_cita: UUID,
    payload: CitaObservacionesUpdate,
    db: Session = Depends(get_db),
):
    return servicio.actualizar_observaciones(db, id_cita, payload)
