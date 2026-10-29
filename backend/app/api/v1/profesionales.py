"""Endpoints de profesionales."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.comun import rut_de_ruta
from app.api.deps import get_usuario_actual, requiere_administrador
from app.db.session import get_db
from app.schemas.common import Pagina
from app.schemas.profesional import (
    ProfesionalCreate,
    ProfesionalOut,
    ProfesionalUpdate,
)
from app.services import profesionales as servicio

router = APIRouter(prefix="/profesionales", tags=["profesionales"])


@router.get(
    "",
    response_model=Pagina[ProfesionalOut],
    summary="Listar profesionales",
    dependencies=[Depends(get_usuario_actual)],
)
def listar(
    rut: str | None = Query(default=None, description="Busqueda parcial por RUT"),
    especialidad: str | None = None,
    activo: bool | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return servicio.listar(
        db,
        rut=rut,
        especialidad=especialidad,
        activo=activo,
        pagina=page,
        por_pagina=per_page,
    )


@router.post(
    "",
    response_model=ProfesionalOut,
    status_code=201,
    summary="Crear profesional",
    dependencies=[Depends(requiere_administrador)],
)
def crear(payload: ProfesionalCreate, db: Session = Depends(get_db)):
    return servicio.crear(db, payload)


@router.get(
    "/{rut}",
    response_model=ProfesionalOut,
    summary="Obtener profesional",
    dependencies=[Depends(get_usuario_actual)],
)
def obtener(rut: str, db: Session = Depends(get_db)):
    return servicio.obtener_o_404(db, rut_de_ruta(rut))


@router.patch(
    "/{rut}",
    response_model=ProfesionalOut,
    summary="Modificar profesional",
    dependencies=[Depends(requiere_administrador)],
)
def actualizar(
    rut: str,
    payload: ProfesionalUpdate,
    db: Session = Depends(get_db),
):
    return servicio.actualizar(db, rut_de_ruta(rut), payload)
