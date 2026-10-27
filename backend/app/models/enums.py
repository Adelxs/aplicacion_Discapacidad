"""Enumeraciones de dominio compartidas por modelos y servicios."""

from enum import Enum


class RolUsuario(str, Enum):
    ADMINISTRADOR = "administrador"
    PROFESIONAL = "profesional"


class EstadoCita(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    ATENDIDA = "atendida"
    CANCELADA = "cancelada"
    AUSENTE = "ausente"


ESTADOS_CITA_ACTIVOS = (
    EstadoCita.PENDIENTE.value,
    EstadoCita.CONFIRMADA.value,
)

ESTADOS_CITA_TERMINALES = (
    EstadoCita.ATENDIDA.value,
    EstadoCita.CANCELADA.value,
    EstadoCita.AUSENTE.value,
)
