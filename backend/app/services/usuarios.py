"""Logica de negocio de usuarios."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ErrorAPI
from app.core.security import hashear_password
from app.models import RolUsuario, Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.services.paginacion import paginar


def obtener_o_404(db: Session, rut: str) -> Usuario:
    usuario = db.get(Usuario, rut)
    if usuario is None:
        raise ErrorAPI(
            status_code=404,
            mensaje="Usuario no encontrado.",
            codigo="no_encontrado",
        )
    return usuario


def crear(db: Session, datos: UsuarioCreate) -> Usuario:
    usuario = Usuario(
        rut=datos.rut,
        nombres=datos.nombres,
        apellidos=datos.apellidos,
        correo_electronico=datos.correo_electronico,
        password_hash=hashear_password(datos.password),
        rol=datos.rol,
        activo=datos.activo,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorAPI(
            status_code=409,
            mensaje="Ya existe un usuario con ese RUT.",
            codigo="conflicto",
        ) from None
    db.refresh(usuario)
    return usuario


def actualizar(db: Session, rut: str, datos: UsuarioUpdate) -> Usuario:
    usuario = obtener_o_404(db, rut)
    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorAPI(
            status_code=409,
            mensaje="No fue posible actualizar el usuario.",
            codigo="conflicto",
        ) from None
    db.refresh(usuario)
    return usuario


def listar(
    db: Session,
    *,
    rut: str | None,
    rol: RolUsuario | None,
    activo: bool | None,
    pagina: int,
    por_pagina: int,
) -> dict:
    consulta = select(Usuario)
    if rut:
        consulta = consulta.where(Usuario.rut.ilike(f"%{rut.replace('.', '')}%"))
    if rol is not None:
        consulta = consulta.where(Usuario.rol == rol)
    if activo is not None:
        consulta = consulta.where(Usuario.activo == activo)

    consulta = consulta.order_by(Usuario.apellidos, Usuario.nombres, Usuario.rut)
    return paginar(db, consulta, pagina, por_pagina)
