"""Logica de negocio y almacenamiento privado de documentos.

Los archivos se guardan fuera de la base de datos, con un nombre generado por
el servidor. Nunca se usa el nombre enviado por el cliente para construir la
ruta, y el contenido se valida por sus primeros bytes, no por el
`Content-Type` declarado.
"""

import uuid
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import desc, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ErrorAPI
from app.core.rut import normalizar_rut
from app.models import Atencion, Documento, Paciente, RolUsuario, Usuario
from app.services.paginacion import paginar

FIRMAS = (
    ("application/pdf", b"%PDF-"),
    ("image/jpeg", b"\xff\xd8\xff"),
    ("image/png", b"\x89PNG\r\n\x1a\n"),
)
EXTENSIONES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}
BLOQUE = 1024 * 1024


def _detectar_tipo(cabecera: bytes) -> str | None:
    for tipo, firma in FIRMAS:
        if cabecera.startswith(firma):
            return tipo
    return None


def _nombre_seguro(nombre: str | None, extension: str) -> str:
    """Descarta rutas y caracteres peligrosos del nombre original."""
    base = Path(nombre or "").name.strip()
    if not base or base in {".", ".."}:
        base = f"documento{extension}"
    return base[:255]


def _guardar(archivo: UploadFile) -> tuple[str, str, int, str]:
    cabecera = archivo.file.read(8)
    tipo = _detectar_tipo(cabecera)
    if tipo is None:
        raise ErrorAPI(
            status_code=415,
            mensaje="Solo se permiten documentos PDF, JPEG o PNG.",
            codigo="tipo_no_permitido",
        )
    archivo.file.seek(0)

    extension = EXTENSIONES[tipo]
    nombre_original = _nombre_seguro(archivo.filename, extension)

    directorio = Path(settings.documentos_dir)
    directorio.mkdir(parents=True, exist_ok=True)

    clave = f"{uuid.uuid4().hex}{extension}"
    destino = directorio / clave
    limite = settings.max_documento_bytes
    tamano = 0

    try:
        with destino.open("wb") as salida:
            while bloque := archivo.file.read(BLOQUE):
                tamano += len(bloque)
                if tamano > limite:
                    raise ErrorAPI(
                        status_code=413,
                        mensaje=(
                            "El archivo supera el maximo permitido de "
                            f"{settings.max_documento_mb} MB."
                        ),
                        codigo="archivo_demasiado_grande",
                    )
                salida.write(bloque)
    except Exception:
        destino.unlink(missing_ok=True)
        raise

    return clave, tipo, tamano, nombre_original


def _es_visible(db: Session, documento: Documento, usuario: Usuario) -> bool:
    if usuario.rol == RolUsuario.ADMINISTRADOR:
        return True
    if documento.subido_por_rut == usuario.rut:
        return True
    if documento.id_atencion is None:
        return False
    atencion = db.get(Atencion, documento.id_atencion)
    return atencion is not None and atencion.profesional_rut == usuario.rut


def obtener_visible(
    db: Session, id_documento: UUID, usuario: Usuario
) -> Documento:
    documento = db.get(Documento, id_documento)
    if documento is None or not _es_visible(db, documento, usuario):
        raise ErrorAPI(
            status_code=404,
            mensaje="Documento no encontrado.",
            codigo="no_encontrado",
        )
    return documento


def crear(
    db: Session,
    usuario: Usuario,
    paciente_rut: str,
    id_atencion: UUID | None,
    archivo: UploadFile,
) -> Documento:
    try:
        rut = normalizar_rut(paciente_rut)
    except ValueError:
        raise ErrorAPI(
            status_code=422,
            mensaje="El RUT del paciente no es valido.",
            codigo="datos_invalidos",
        ) from None

    paciente = db.get(Paciente, rut)
    if paciente is None:
        raise ErrorAPI(
            status_code=404,
            mensaje="Paciente no encontrado.",
            codigo="no_encontrado",
        )

    if id_atencion is not None:
        atencion = db.get(Atencion, id_atencion)
        if atencion is None or (
            usuario.rol != RolUsuario.ADMINISTRADOR
            and atencion.profesional_rut != usuario.rut
        ):
            raise ErrorAPI(
                status_code=404,
                mensaje="Atencion no encontrada.",
                codigo="no_encontrado",
            )
        if atencion.paciente_rut != paciente.rut:
            raise ErrorAPI(
                status_code=422,
                mensaje="La atencion no corresponde al paciente indicado.",
                codigo="datos_invalidos",
            )

    clave, tipo_mime, tamano, nombre_original = _guardar(archivo)

    documento = Documento(
        paciente_rut=paciente.rut,
        id_atencion=id_atencion,
        nombre_original=nombre_original,
        tipo_mime=tipo_mime,
        tamano_bytes=tamano,
        clave_archivo=clave,
        subido_por_rut=usuario.rut,
    )
    db.add(documento)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        (Path(settings.documentos_dir) / clave).unlink(missing_ok=True)
        raise ErrorAPI(
            status_code=409,
            mensaje="No fue posible registrar el documento.",
            codigo="conflicto",
        ) from None

    db.refresh(documento)
    return documento


def ruta_fisica(documento: Documento) -> Path:
    ruta = Path(settings.documentos_dir) / documento.clave_archivo
    if not ruta.is_file():
        raise ErrorAPI(
            status_code=404,
            mensaje="El archivo del documento no esta disponible.",
            codigo="no_encontrado",
        )
    return ruta


def eliminar(db: Session, id_documento: UUID, usuario: Usuario) -> None:
    documento = obtener_visible(db, id_documento, usuario)
    if documento.subido_por_rut != usuario.rut:
        if usuario.rol == RolUsuario.ADMINISTRADOR:
            raise ErrorAPI(
                status_code=403,
                mensaje="Solo quien subio el documento puede eliminarlo.",
                codigo="sin_permisos",
            )
        raise ErrorAPI(
            status_code=404,
            mensaje="Documento no encontrado.",
            codigo="no_encontrado",
        )

    ruta = Path(settings.documentos_dir) / documento.clave_archivo
    db.delete(documento)
    db.commit()
    ruta.unlink(missing_ok=True)


def listar(
    db: Session,
    usuario: Usuario,
    *,
    paciente_rut: str | None,
    pagina: int,
    por_pagina: int,
) -> dict:
    consulta = select(Documento)

    if usuario.rol != RolUsuario.ADMINISTRADOR:
        de_sus_atenciones = select(Atencion.id_atencion).where(
            Atencion.profesional_rut == usuario.rut
        )
        consulta = consulta.where(
            or_(
                Documento.subido_por_rut == usuario.rut,
                Documento.id_atencion.in_(de_sus_atenciones),
            )
        )

    if paciente_rut:
        consulta = consulta.where(
            Documento.paciente_rut.ilike(f"%{paciente_rut.replace('.', '')}%")
        )

    consulta = consulta.order_by(
        desc(Documento.fecha_creacion), desc(Documento.id_documento)
    )
    return paginar(db, consulta, pagina, por_pagina)
