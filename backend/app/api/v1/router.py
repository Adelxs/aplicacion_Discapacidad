"""Enrutador principal de la version 1 de la API."""

from fastapi import APIRouter

from app.api.v1 import auth, health, pacientes, profesionales, usuarios

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(usuarios.router)
api_router.include_router(profesionales.router)
api_router.include_router(pacientes.router)
