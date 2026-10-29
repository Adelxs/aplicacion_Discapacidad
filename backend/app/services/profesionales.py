"""Logica de negocio de profesionales."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ErrorAPI
from app.models import Profesional, RolUsuario, Usuario
from app.schemas.profesional import ProfesionalCreate, ProfesionalUpdate
from app.services.paginacion import paginar


def obtener_o_404(db: Session, rut: str) -> Profesional:
    profesional = db.get(Profesional, rut)
    if profesional is None:
        raise ErrorAPI(
            status_code=404,
            mensaje="Profesional no encontrado.",
            codigo="no_encontrado",
        )
    return profesional


def _validar_cuenta_vinculada(
    db: Session, rut_profesional: str, usuario_rut: str | None
) -> None:
    if usuario_rut is None:
        return

    if usuario_rut != rut_profesional:
        raise ErrorAPI(
            status_code=422,
            mensaje="El RUT de la cuenta debe coincidir con el del profesional.",
            codigo="datos_invalidos",
        )

    usuario = db.get(Usuario, usuario_rut)
    if usuario is None:
        raise ErrorAPI(
            status_code=404,
            mensaje="La cuenta indicada no existe.",
            codigo="no_encontrado",
        )
    if usuario.rol != RolUsuario.PROFESIONAL:
        raise ErrorAPI(
            status_code=409,
            mensaje="La cuenta vinculada debe tener rol profesional.",
            codigo="conflicto",
        )


def crear(db: Session, datos: ProfesionalCreate) -> Profesional:
    _validar_cuenta_vinculada(db, datos.rut, datos.usuario_rut)

    profesional = Profesional(
        rut=datos.rut,
        nombres=datos.nombres,
        apellidos=datos.apellidos,
        especialidad=datos.especialidad,
        telefono=datos.telefono,
        correo_electronico=datos.correo_electronico,
        usuario_rut=datos.usuario_rut,
        activo=datos.activo,
    )
    db.add(profesional)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorAPI(
            status_code=409,
            mensaje="Ya existe un profesional con ese RUT o esa cuenta ya esta vinculada.",
            codigo="conflicto",
        ) from None
    db.refresh(profesional)
    return profesional


def actualizar(
    db: Session, rut: str, datos: ProfesionalUpdate
) -> Profesional:
    profesional = obtener_o_404(db, rut)
    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)

    if "usuario_rut" in cambios:
        _validar_cuenta_vinculada(db, rut, cambios["usuario_rut"])

    for campo, valor in cambios.items():
        setattr(profesional, campo, valor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorAPI(
            status_code=409,
            mensaje="No fue posible actualizar el profesional.",
            codigo="conflicto",
        ) from None
    db.refresh(profesional)
    return profesional


def listar(
    db: Session,
    *,
    rut: str | None,
    especialidad: str | None,
    activo: bool | None,
    pagina: int,
    por_pagina: int,
) -> dict:
    consulta = select(Profesional)
    if rut:
        consulta = consulta.where(
            Profesional.rut.ilike(f"%{rut.replace('.', '')}%")
        )
    if especialidad:
        consulta = consulta.where(
            Profesional.especialidad.ilike(f"%{especialidad}%")
        )
    if activo is not None:
        consulta = consulta.where(Profesional.activo == activo)

    consulta = consulta.order_by(
        Profesional.apellidos, Profesional.nombres, Profesional.rut
    )
    return paginar(db, consulta, pagina, por_pagina)
