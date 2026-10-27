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
| ORM / migraciones | SQLAlchemy 2 + Alembic |
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

## Base de datos y migraciones

La primera vez (y tras cada nueva migración) hay que aplicar el esquema:

```bash
docker compose exec backend alembic upgrade head
```

Otros comandos útiles:

```bash
# Version aplicada actualmente
docker compose exec backend alembic current

# Verificar que los modelos ORM coinciden con la base de datos
docker compose exec backend alembic check

# Crear una migracion nueva tras cambiar los modelos (revisar el archivo generado)
docker compose exec backend alembic revision --autogenerate -m "descripcion del cambio"
```

Reglas de la Etapa 2 reflejadas en el esquema:

- RUT canonico (`12345678-9`, sin puntos) validado por restriccion `CHECK`.
- Una cita no puede terminar antes de empezar.
- Estados de cita limitados a los cinco permitidos.
- Una atencion por cita y coherencia de paciente/profesional con la cita.
- Documentos asociados a una atencion deben pertenecer al mismo paciente.
- Solapamientos de agenda bloqueados en la base de datos con
  `EXCLUDE USING gist`, incluidas solicitudes concurrentes. Las citas canceladas
  liberan el horario.
- Pacientes con historial (`citas`, `atenciones`, `documentos`) no pueden
  eliminarse fisicamente (`ON DELETE RESTRICT`).

## Autenticación

| Método | Endpoint | Función |
|---|---|---|
| POST | `/api/v1/auth/login` | Autentica con RUT y contraseña. |
| GET | `/api/v1/auth/me` | Devuelve la identidad del usuario autenticado. |

- Contraseñas almacenadas con **Argon2id**; nunca en texto plano.
- Token **JWT** firmado con `HS256` y `SECRET_KEY`, con expiración obligatoria.
- El token solo contiene `sub` (RUT), `rol`, `iat` y `exp`: sin contraseñas ni
  información clínica.
- Los mensajes de error de login no revelan si el RUT existe.
- Una cuenta desactivada pierde acceso de inmediato, aunque su token siga vigente.
- La autorización por rol se verifica en el backend con la dependencia
  `requiere_roles`; ocultar botones en React no sustituye ese control.

### Crear la cuenta administradora inicial

No hay registro público: la primera cuenta se crea por consola.

```bash
docker compose exec backend python -m app.cli.crear_admin \
  --rut 11111111-1 --nombres Ana --apellidos Administradora \
  --correo ana@ejemplo.cl
```

La contraseña se solicita de forma interactiva, de modo que no queda en el
historial de comandos ni en los logs.

## Pruebas automatizadas

```bash
docker compose exec backend pytest -v
```

Las pruebas de integracion crean una base de datos aparte
(`citas_municipales_test`), aplican las migraciones desde cero y la eliminan al
terminar. Nunca usan la base de datos de desarrollo ni datos reales.

## Variables de entorno

| Variable | Descripción |
|---|---|
| `POSTGRES_DB` | Nombre de la base de datos. |
| `POSTGRES_USER` | Usuario de la base de datos. |
| `POSTGRES_PASSWORD` | Contraseña de la base de datos. No se versiona. |
| `SECRET_KEY` | Secreto para la firma de JWT. |
| `ENTORNO` | `desarrollo`, `pruebas` o `produccion`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Vigencia del token de acceso en minutos (480 por defecto). |
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
│  ├─ alembic.ini
│  ├─ migrations/              # Entorno de Alembic y versiones del esquema
│  ├─ tests/                   # Pruebas pytest
│  └─ app/
│     ├─ main.py               # Aplicación FastAPI
│     ├─ core/config.py        # Configuración desde variables de entorno
│     ├─ core/errors.py        # Manejo uniforme de errores
│     ├─ core/rut.py           # Normalización y validación de RUT
│     ├─ core/security.py      # Argon2id y JWT
│     ├─ api/deps.py           # Autenticación y autorización por rol
│     ├─ schemas/              # Esquemas Pydantic de entrada/salida
│     ├─ cli/                  # Comandos administrativos (crear_admin)
│     ├─ db/base.py            # Base declarativa de SQLAlchemy
│     ├─ db/session.py         # Motor y sesiones
│     ├─ models/               # Modelos ORM (una entidad por archivo)
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
| 1 | Estructura, configuración, Docker Compose y salud | Completada |
| 2 | Modelos ORM y migraciones Alembic | Completada |
| 3 | Autenticación y autorización | Completada |
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
