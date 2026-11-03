"""Configuracion central de la aplicacion, leida desde variables de entorno."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Sistema Municipal de Citas y Atenciones"
    app_version: str = "0.1.0"
    entorno: str = "desarrollo"
    api_v1_prefix: str = "/api/v1"
    zona_horaria: str = "America/Santiago"

    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/citas"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalizar_database_url(cls, valor: object) -> object:
        # Neon, Render y otros proveedores entregan la URL con el esquema
        # "postgresql://", que SQLAlchemy interpreta como psycopg2. La app usa
        # psycopg 3, por lo que se normaliza el esquema automaticamente.
        if isinstance(valor, str):
            if valor.startswith("postgresql://"):
                return "postgresql+psycopg://" + valor[len("postgresql://") :]
            if valor.startswith("postgres://"):
                return "postgresql+psycopg://" + valor[len("postgres://") :]
        return valor

    secret_key: str = "cambiar-en-entorno-real"
    jwt_algorithm: str = "HS256"
    # Jornada laboral: el MVP no incluye refresh tokens.
    access_token_expire_minutes: int = 480
    password_min_length: int = 8

    cors_origins: list[str] = ["http://localhost:5173"]

    documentos_dir: str = "/data/documentos"
    max_documento_mb: int = 10

    @property
    def max_documento_bytes(self) -> int:
        return self.max_documento_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
