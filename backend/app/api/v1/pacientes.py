"""Endpoints de pacientes."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.comun import rut_de_ruta
from app.api.deps import get_usuario_actual, requiere_administrador
from app.db.session import get_db
from app.schemas.common import Pagina
from app.schemas.paciente import PacienteCreate, PacienteOut, PacienteUpdate
from app.services import pacientes as servicio

router = APIRouter(prefix="/pacientes", tags=["pacientes"])


@router.get(
    "",
    response_model=Pagina[PacienteOut],
    summary="Listar pacientes",
    dependencies=[Depends(get_usuario_actual)],
)
def listar(
    rut: str | None = Query(default=None, description="Busqueda parcial por RUT"),
    activo: bool | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return servicio.listar(
        db,
        rut=rut,
        activo=activo,
        pagina=page,
        por_pagina=per_page,
    )


@router.post(
    "",
    response_model=PacienteOut,
    status_code=201,
    summary="Crear paciente",
    dependencies=[Depends(requiere_administrador)],
)
def crear(payload: PacienteCreate, db: Session = Depends(get_db)):
    return servicio.crear(db, payload)


@router.get(
    "/{rut}",
    response_model=PacienteOut,
    summary="Obtener paciente",
    dependencies=[Depends(get_usuario_actual)],
)
def obtener(rut: str, db: Session = Depends(get_db)):
    return servicio.obtener_o_404(db, rut_de_ruta(rut))


@router.patch(
    "/{rut}",
    response_model=PacienteOut,
    summary="Modificar paciente",
    dependencies=[Depends(requiere_administrador)],
)
def actualizar(
    rut: str,
    payload: PacienteUpdate,
    db: Session = Depends(get_db),
):
    return servicio.actualizar(db, rut_de_ruta(rut), payload)


@router.delete(
    "/{rut}",
    status_code=204,
    response_class=Response,
    summary="Eliminar paciente sin historial",
    dependencies=[Depends(requiere_administrador)],
)
def eliminar(rut: str, db: Session = Depends(get_db)) -> Response:
    servicio.eliminar(db, rut_de_ruta(rut))
    return Response(status_code=204)
