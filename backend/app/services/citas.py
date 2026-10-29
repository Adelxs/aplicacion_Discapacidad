"""Logica de negocio de citas y agenda."""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ErrorAPI
from app.core.tiempo import inicio_del_dia
from app.models import (
    Cita,
    EstadoCita,
    Paciente,
    Profesional,
    RolUsuario,
    Usuario,
)
from app.schemas.cita import CitaCreate, CitaObservacionesUpdate
from app.services.paginacion import paginar

# Transiciones permitidas. `atendida` se alcanza al registrar la atencion
# (Etapa 6); aqui no existe un endpoint para fijarla manualmente.
TRANSICIONES: dict[EstadoCita, set[EstadoCita]] = {
    EstadoCita.PENDIENTE: {EstadoCita.CONFIRMADA, EstadoCita.CANCELADA},
    EstadoCita.CONFIRMADA: {
        EstadoCita.ATENDIDA,
        EstadoCita.CANCELADA,
        EstadoCita.AUSENTE,
    },
    EstadoCita.ATENDIDA: set(),
    EstadoCita.CANCELADA: set(),
    EstadoCita.AUSENTE: set(),
}


def obtener_o_404(db: Session, id_cita: UUID) -> Cita:
    cita = db.get(Cita, id_cita)
    if cita is None:
        raise ErrorAPI(
            status_code=404,
            mensaje="Cita no encontrada.",
            codigo="no_encontrado",
        )
    return cita


def obtener_visible(db: Session, id_cita: UUID, usuario: Usuario) -> Cita:
    """Devuelve la cita si el usuario puede verla.

    Un profesional solo accede a su propia agenda; para el resto se responde
    404, igual que si la cita no existiera, para no revelar su existencia.
    """
    cita = obtener_o_404(db, id_cita)
    if (
        usuario.rol != RolUsuario.ADMINISTRADOR
        and cita.profesional_rut != usuario.rut
    ):
        raise ErrorAPI(
            status_code=404,
            mensaje="Cita no encontrada.",
            codigo="no_encontrado",
        )
    return cita


def _hay_solapamiento(
    db: Session,
    profesional_rut: str,
    inicio,
    fin,
) -> bool:
    consulta = (
        select(Cita.id_cita)
        .where(
            Cita.profesional_rut == profesional_rut,
            Cita.estado != EstadoCita.CANCELADA,
            Cita.fecha_hora_inicio < fin,
            Cita.fecha_hora_fin > inicio,
        )
        .limit(1)
    )
    return db.scalar(consulta) is not None


def _conflicto_horario() -> ErrorAPI:
    return ErrorAPI(
        status_code=409,
        mensaje="El profesional ya tiene una cita en ese horario.",
        codigo="conflicto",
    )


def crear(db: Session, datos: CitaCreate, usuario: Usuario) -> Cita:
    profesional = db.get(Profesional, usuario.rut)
    if profesional is None or not profesional.activo:
        raise ErrorAPI(
            status_code=409,
            mensaje=(
                "La cuenta no tiene un perfil profesional activo para agendar."
            ),
            codigo="conflicto",
        )

    paciente = db.get(Paciente, datos.paciente_rut)
    if paciente is None:
        raise ErrorAPI(
            status_code=404,
            mensaje="Paciente no encontrado.",
            codigo="no_encontrado",
        )
    if not paciente.activo:
        raise ErrorAPI(
            status_code=409,
            mensaje="El paciente esta inactivo y no puede agendar citas.",
            codigo="conflicto",
        )

    # Comprobacion explicita para dar un mensaje claro; la restriccion EXCLUDE
    # sigue protegiendo ante solicitudes concurrentes.
    if _hay_solapamiento(
        db, usuario.rut, datos.fecha_hora_inicio, datos.fecha_hora_fin
    ):
        raise _conflicto_horario()

    cita = Cita(
        paciente_rut=datos.paciente_rut,
        profesional_rut=usuario.rut,
        fecha_hora_inicio=datos.fecha_hora_inicio,
        fecha_hora_fin=datos.fecha_hora_fin,
        motivo=datos.motivo,
        estado=EstadoCita.PENDIENTE,
        creado_por_rut=usuario.rut,
    )
    db.add(cita)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _conflicto_horario() from None
    db.refresh(cita)
    return cita


def cambiar_estado(
    db: Session,
    id_cita: UUID,
    usuario: Usuario,
    nuevo: EstadoCita,
) -> Cita:
    cita = obtener_visible(db, id_cita, usuario)
    if cita.profesional_rut != usuario.rut:
        raise ErrorAPI(
            status_code=404,
            mensaje="Cita no encontrada.",
            codigo="no_encontrado",
        )

    if nuevo not in TRANSICIONES[cita.estado]:
        raise ErrorAPI(
            status_code=409,
            mensaje=(
                "No se puede cambiar la cita de "
                f"'{cita.estado.value}' a '{nuevo.value}'."
            ),
            codigo="conflicto",
        )

    cita.estado = nuevo
    db.commit()
    db.refresh(cita)
    return cita


def actualizar_observaciones(
    db: Session,
    id_cita: UUID,
    datos: CitaObservacionesUpdate,
) -> Cita:
    cita = obtener_o_404(db, id_cita)
    cita.observaciones_administrativas = datos.observaciones_administrativas
    db.commit()
    db.refresh(cita)
    return cita


def listar(
    db: Session,
    usuario: Usuario,
    *,
    paciente_rut: str | None,
    estado: EstadoCita | None,
    desde: date | None,
    hasta: date | None,
    pagina: int,
    por_pagina: int,
) -> dict:
    consulta = select(Cita)

    if usuario.rol != RolUsuario.ADMINISTRADOR:
        consulta = consulta.where(Cita.profesional_rut == usuario.rut)

    if paciente_rut:
        consulta = consulta.where(
            Cita.paciente_rut.ilike(f"%{paciente_rut.replace('.', '')}%")
        )
    if estado is not None:
        consulta = consulta.where(Cita.estado == estado)
    if desde is not None:
        consulta = consulta.where(
            Cita.fecha_hora_inicio >= inicio_del_dia(desde)
        )
    if hasta is not None:
        consulta = consulta.where(
            Cita.fecha_hora_inicio < inicio_del_dia(hasta + timedelta(days=1))
        )

    consulta = consulta.order_by(Cita.fecha_hora_inicio, Cita.id_cita)
    return paginar(db, consulta, pagina, por_pagina)
