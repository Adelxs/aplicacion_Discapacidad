"""Logica de negocio de atenciones."""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ErrorAPI
from app.core.tiempo import inicio_del_dia
from app.models import Atencion, Cita, EstadoCita, RolUsuario, Usuario
from app.schemas.atencion import AtencionCreate, AtencionUpdate
from app.services.paginacion import paginar


def _no_encontrada() -> ErrorAPI:
    return ErrorAPI(
        status_code=404,
        mensaje="Atencion no encontrada.",
        codigo="no_encontrado",
    )


def obtener_visible(db: Session, id_atencion: UUID, usuario: Usuario) -> Atencion:
    """Administrador ve todas; el profesional solo las propias."""
    atencion = db.get(Atencion, id_atencion)
    if atencion is None:
        raise _no_encontrada()
    if (
        usuario.rol != RolUsuario.ADMINISTRADOR
        and atencion.profesional_rut != usuario.rut
    ):
        raise _no_encontrada()
    return atencion


def crear(db: Session, datos: AtencionCreate, usuario: Usuario) -> Atencion:
    """Registra la atencion y pasa la cita a `atendida` en una sola transaccion."""
    cita = db.get(Cita, datos.id_cita)
    if cita is None or cita.profesional_rut != usuario.rut:
        raise ErrorAPI(
            status_code=404,
            mensaje="Cita no encontrada.",
            codigo="no_encontrado",
        )

    if cita.estado != EstadoCita.CONFIRMADA:
        raise ErrorAPI(
            status_code=409,
            mensaje=(
                "Solo se puede registrar la atencion de una cita confirmada. "
                f"Estado actual: '{cita.estado.value}'."
            ),
            codigo="conflicto",
        )

    if not (
        cita.fecha_hora_inicio
        <= datos.fecha_atencion
        <= cita.fecha_hora_fin
    ):
        raise ErrorAPI(
            status_code=422,
            mensaje=(
                "La fecha de la atencion debe estar dentro del horario de la "
                "cita."
            ),
            codigo="datos_invalidos",
        )

    atencion = Atencion(
        id_cita=cita.id_cita,
        paciente_rut=cita.paciente_rut,
        profesional_rut=cita.profesional_rut,
        fecha_atencion=datos.fecha_atencion,
        motivo=datos.motivo,
        registro_clinico=datos.registro_clinico,
        creado_por_rut=usuario.rut,
    )
    cita.estado = EstadoCita.ATENDIDA
    db.add(atencion)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorAPI(
            status_code=409,
            mensaje="La cita ya tiene una atencion registrada.",
            codigo="conflicto",
        ) from None

    db.refresh(atencion)
    return atencion


def actualizar(
    db: Session,
    id_atencion: UUID,
    datos: AtencionUpdate,
    usuario: Usuario,
) -> Atencion:
    atencion = obtener_visible(db, id_atencion, usuario)
    if atencion.profesional_rut != usuario.rut:
        raise _no_encontrada()

    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
    for campo, valor in cambios.items():
        setattr(atencion, campo, valor)

    db.commit()
    db.refresh(atencion)
    return atencion


def listar(
    db: Session,
    usuario: Usuario,
    *,
    paciente_rut: str | None,
    desde: date | None,
    hasta: date | None,
    pagina: int,
    por_pagina: int,
) -> dict:
    consulta = select(Atencion)

    if usuario.rol != RolUsuario.ADMINISTRADOR:
        consulta = consulta.where(Atencion.profesional_rut == usuario.rut)

    if paciente_rut:
        consulta = consulta.where(
            Atencion.paciente_rut.ilike(f"%{paciente_rut.replace('.', '')}%")
        )
    if desde is not None:
        consulta = consulta.where(
            Atencion.fecha_atencion >= inicio_del_dia(desde)
        )
    if hasta is not None:
        consulta = consulta.where(
            Atencion.fecha_atencion < inicio_del_dia(hasta + timedelta(days=1))
        )

    consulta = consulta.order_by(
        desc(Atencion.fecha_atencion), desc(Atencion.id_atencion)
    )
    return paginar(db, consulta, pagina, por_pagina)
