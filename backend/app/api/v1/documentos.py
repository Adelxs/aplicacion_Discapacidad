"""Endpoints de documentos privados."""

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_actual
from app.db.session import get_db
from app.models import Usuario
from app.schemas.common import Pagina
from app.schemas.documento import DocumentoOut
from app.services import documentos as servicio

router = APIRouter(prefix="/documentos", tags=["documentos"])


@router.get("", response_model=Pagina[DocumentoOut], summary="Listar documentos")
def listar(
    paciente_rut: str | None = Query(
        default=None, description="Busqueda parcial por RUT del paciente"
    ),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    return servicio.listar(
        db,
        usuario,
        paciente_rut=paciente_rut,
        pagina=page,
        por_pagina=per_page,
    )


@router.post(
    "",
    response_model=DocumentoOut,
    status_code=201,
    summary="Subir un documento",
)
def subir(
    paciente_rut: str = Form(...),
    archivo: UploadFile = File(...),
    id_atencion: UUID | None = Form(default=None),
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    return servicio.crear(db, usuario, paciente_rut, id_atencion, archivo)


@router.get(
    "/{id_documento}",
    response_model=DocumentoOut,
    summary="Obtener metadatos del documento",
)
def obtener(
    id_documento: UUID,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    return servicio.obtener_visible(db, id_documento, usuario)


@router.get("/{id_documento}/archivo", summary="Descargar el documento")
def descargar(
    id_documento: UUID,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    documento = servicio.obtener_visible(db, id_documento, usuario)
    return FileResponse(
        servicio.ruta_fisica(documento),
        media_type=documento.tipo_mime,
        filename=documento.nombre_original,
    )


@router.delete(
    "/{id_documento}",
    status_code=204,
    response_class=Response,
    summary="Eliminar un documento propio",
)
def eliminar(
    id_documento: UUID,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
) -> Response:
    servicio.eliminar(db, id_documento, usuario)
    return Response(status_code=204)
