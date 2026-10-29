"""Endpoints de usuarios (solo administrador)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.comun import rut_de_ruta
from app.api.deps import requiere_administrador
from app.db.session import get_db
from app.models import RolUsuario
from app.schemas.common import Pagina
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services import usuarios as servicio

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(requiere_administrador)],
)


@router.get("", response_model=Pagina[UsuarioOut], summary="Listar usuarios")
def listar(
    rut: str | None = Query(default=None, description="Busqueda parcial por RUT"),
    rol: RolUsuario | None = None,
    activo: bool | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return servicio.listar(
        db,
        rut=rut,
        rol=rol,
        activo=activo,
        pagina=page,
        por_pagina=per_page,
    )


@router.post(
    "",
    response_model=UsuarioOut,
    status_code=201,
    summary="Crear usuario",
)
def crear(payload: UsuarioCreate, db: Session = Depends(get_db)):
    return servicio.crear(db, payload)


@router.get("/{rut}", response_model=UsuarioOut, summary="Obtener usuario")
def obtener(rut: str, db: Session = Depends(get_db)):
    return servicio.obtener_o_404(db, rut_de_ruta(rut))


@router.patch("/{rut}", response_model=UsuarioOut, summary="Modificar usuario")
def actualizar(
    rut: str,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
):
    return servicio.actualizar(db, rut_de_ruta(rut), payload)
