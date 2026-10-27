"""Punto de entrada de la API."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import registrar_manejadores

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.documentos_dir).mkdir(parents=True, exist_ok=True)
    if len(settings.secret_key) < 32:
        logger.warning(
            "SECRET_KEY tiene menos de 32 caracteres. Configure un secreto seguro."
        )
    logger.info("Servicio iniciado en entorno '%s'.", settings.entorno)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API del Sistema Municipal de Citas y Atenciones (MVP).",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_manejadores(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
def raiz() -> dict:
    return {
        "servicio": settings.app_name,
        "version": settings.app_version,
        "documentacion": "/docs",
        "salud": f"{settings.api_v1_prefix}/health",
    }
