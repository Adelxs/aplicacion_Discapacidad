"""Logica de negocio de pacientes."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ErrorAPI
from app.models import Atencion, Cita, Documento, Paciente
from app.schemas.paciente import PacienteCreate, PacienteUpdate
from app.services.paginacion import paginar


def obtener_o_404(db: Session, rut: str) -> Paciente:
    paciente = db.get(Paciente, rut)
    if paciente is None:
        raise ErrorAPI(
            status_code=404,
            mensaje="Paciente no encontrado.",
            codigo="no_encontrado",
        )
    return paciente


def crear(db: Session, datos: PacienteCreate) -> Paciente:
    paciente = Paciente(
        rut=datos.rut,
        nombres=datos.nombres,
        apellidos=datos.apellidos,
        fecha_nacimiento=datos.fecha_nacimiento,
        telefono=datos.telefono,
        correo_electronico=datos.correo_electronico,
        direccion=datos.direccion,
        activo=datos.activo,
    )
    db.add(paciente)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorAPI(
            status_code=409,
            mensaje="Ya existe un paciente con ese RUT.",
            codigo="conflicto",
        ) from None
    db.refresh(paciente)
    return paciente


def actualizar(db: Session, rut: str, datos: PacienteUpdate) -> Paciente:
    paciente = obtener_o_404(db, rut)
    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
    for campo, valor in cambios.items():
        setattr(paciente, campo, valor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorAPI(
            status_code=409,
            mensaje="No fue posible actualizar el paciente.",
            codigo="conflicto",
        ) from None
    db.refresh(paciente)
    return paciente


def _tiene_historial(db: Session, rut: str) -> bool:
    consultas = (
        select(Cita.id_cita).where(Cita.paciente_rut == rut).limit(1),
        select(Atencion.id_atencion)
        .where(Atencion.paciente_rut == rut)
        .limit(1),
        select(Documento.id_documento)
        .where(Documento.paciente_rut == rut)
        .limit(1),
    )
    return any(db.scalar(consulta) is not None for consulta in consultas)


def eliminar(db: Session, rut: str) -> None:
    paciente = obtener_o_404(db, rut)

    if _tiene_historial(db, rut):
        raise ErrorAPI(
            status_code=409,
            mensaje=(
                "El paciente tiene historial asociado (citas, atenciones o "
                "documentos) y no puede eliminarse."
            ),
            codigo="conflicto",
        )

    db.delete(paciente)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorAPI(
            status_code=409,
            mensaje="El paciente no puede eliminarse porque tiene historial asociado.",
            codigo="conflicto",
        ) from None


def listar(
    db: Session,
    *,
    rut: str | None,
    activo: bool | None,
    pagina: int,
    por_pagina: int,
) -> dict:
    consulta = select(Paciente)
    if rut:
        consulta = consulta.where(Paciente.rut.ilike(f"%{rut.replace('.', '')}%"))
    if activo is not None:
        consulta = consulta.where(Paciente.activo == activo)

    consulta = consulta.order_by(
        Paciente.apellidos, Paciente.nombres, Paciente.rut
    )
    return paginar(db, consulta, pagina, por_pagina)
