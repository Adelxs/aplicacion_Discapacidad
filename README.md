# Sistema Municipal de Gestión de Citas y Atenciones — MVP

Aplicación web para la administración de pacientes, profesionales, citas, atenciones y
documentos de un centro municipal o comunitario de atención.

Repositorio independiente del proyecto `aplicacion_SSEE`. No se reutiliza código,
configuración ni datos de ese proyecto.

## Stack

| Componente | Tecnología |
|---|---|
| Frontend | React 18 + Vite |
| Backend | FastAPI (Python 3.12) |
| Base de datos | PostgreSQL 17 |
| ORM / migraciones | SQLAlchemy 2 + Alembic (Etapa 2) |
| Autenticación | JWT Bearer (Etapa 3) |
| Contenedores | Docker + Docker Compose |

## Requisitos

- Docker Desktop con Docker Compose v2 o superior.
- Puerto libre: `8000` (API), `5173` (frontend), `5433` (PostgreSQL en el host).
- El puerto `5433` se usa porque `5432` suele estar ocupado por un PostgreSQL local.

## Puesta en marcha

```bash
cp .env.example .env
# Editar .env y definir POSTGRES_PASSWORD y SECRET_KEY propias.
docker compose up --build
```

Con el entorno levantado:

| Servicio | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| Documentación OpenAPI | http://localhost:8000/docs |
| Salud del servicio | http://localhost:8000/api/v1/health |
| Salud de la base de datos | http://localhost:8000/api/v1/health/db |
| PostgreSQL (host) | `localhost:5433` |

Detener el entorno sin borrar datos:

```bash
docker compose down
```

Detener y eliminar volúmenes (**destructivo**, borra base de datos y documentos):

```bash
docker compose down -v
```

## Variables de entorno

| Variable | Descripción |
|---|---|
| `POSTGRES_DB` | Nombre de la base de datos. |
| `POSTGRES_USER` | Usuario de la base de datos. |
| `POSTGRES_PASSWORD` | Contraseña de la base de datos. No se versiona. |
| `SECRET_KEY` | Secreto para la firma de JWT (se usa desde la Etapa 3). |
| `ENTORNO` | `desarrollo`, `pruebas` o `produccion`. |
| `MAX_DOCUMENTO_MB` | Tamaño máximo permitido por documento. |
| `VITE_API_URL` | URL base de la API consumida por el frontend. |

Generar un secreto nuevo:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Estructura del proyecto

```
aplicacion_DISS/
├─ docker-compose.yml
├─ .env.example
├─ backend/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ app/
│     ├─ main.py               # Aplicación FastAPI
│     ├─ core/config.py        # Configuración desde variables de entorno
│     ├─ core/errors.py        # Manejo uniforme de errores
│     ├─ db/base.py            # Base declarativa de SQLAlchemy
│     ├─ db/session.py         # Motor y sesiones
│     └─ api/v1/               # Rutas de la API v1
└─ frontend/
   ├─ Dockerfile
   ├─ vite.config.js
   └─ src/                     # Aplicación React
```

## Volúmenes persistentes

| Volumen | Uso |
|---|---|
| `diss_postgres_data` | Datos de PostgreSQL. |
| `diss_documentos_data` | Archivos de documentos (acceso privado, fuera de PostgreSQL). |

Los volúmenes **no sustituyen** a las copias de seguridad. El procedimiento de respaldo y
restauración se documentará en la etapa de integración.

## Estado de implementación

| Etapa | Descripción | Estado |
|---|---|---|
| 1 | Estructura, configuración, Docker Compose y salud | En curso |
| 2 | Modelos ORM y migraciones Alembic | Pendiente |
| 3 | Autenticación y autorización | Pendiente |
| 4 | Usuarios, profesionales y pacientes | Pendiente |
| 5 | Citas y agenda | Pendiente |
| 6 | Atenciones | Pendiente |
| 7 | Documentos | Pendiente |
| 8 | Frontend completo | Pendiente |
| 9 | Integración, pruebas y cierre | Pendiente |

## Advertencias

- No usar datos clínicos reales en desarrollo ni en pruebas automatizadas.
- No versionar `.env` ni secretos.
- No ejecutar migraciones destructivas ni eliminar volúmenes sin autorización explícita.
- El proyecto `aplicacion_SSEE` no debe ser modificado.
