"""Registro de modelos. Importar todo aqui permite que Alembic los descubra."""

from app.models.atencion import Atencion
from app.models.cita import Cita
from app.models.documento import Documento
from app.models.enums import EstadoCita, RolUsuario
from app.models.paciente import Paciente
from app.models.profesional import Profesional
from app.models.usuario import Usuario

__all__ = [
    "Atencion",
    "Cita",
    "Documento",
    "EstadoCita",
    "Paciente",
    "Profesional",
    "RolUsuario",
    "Usuario",
]
