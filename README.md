# Sistema Municipal de Gestión de Citas y Atenciones — MVP

Aplicación web para administrar pacientes, profesionales, citas, atenciones y
documentos de un centro municipal o comunitario de atención.

Repositorio independiente del proyecto `aplicacion_SSEE`. No se reutiliza código,
configuración ni datos de ese proyecto. Todo el desarrollo usa datos sintéticos:
**no debe cargarse información clínica real**.

Repositorio: <https://github.com/Adelxs/aplicacion_Discapacidad>.

## Estado

Las nueve etapas del MVP están completas y verificadas. El detalle de pruebas,
decisiones y limitaciones está en [`ESTADO_PROYECTO.md`](ESTADO_PROYECTO.md).
El uso por rol se describe en [`MANUAL_USUARIO.md`](MANUAL_USUARIO.md).

## Stack

| Componente | Tecnología |
|---|---|
| Frontend | React 18.3.1 + Vite 6.4.5 + React Router 7.18.5 |
| Backend | FastAPI 0.115.6 (Python 3.12) |
| Base de datos | PostgreSQL 17 |
| ORM / migraciones | SQLAlchemy 2 + Alembic |
| Autenticación | JWT Bearer (HS256) + Argon2id |
| Contenedores | Docker + Docker Compose |

## Requisitos

- Docker Desktop con Docker Compose v2 o superior.
- Puertos libres: `8000` (API), `5173` (frontend) y `5433` (PostgreSQL en el
  host). El puerto `5433` se usa porque `5432` suele estar ocupado por un
  PostgreSQL local.
- Para las pruebas E2E: Node.js 20 o superior y Chrome o Edge instalado.

## Puesta en marcha

```powershell
Copy-Item .env.example .env
# Editar .env y definir POSTGRES_PASSWORD y SECRET_KEY propias.
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Crear la cuenta administradora inicial (no hay registro público):

```powershell
docker compose exec backend python -m app.cli.crear_admin --rut 11111111-1 --nombres Ana --apellidos Administradora --correo ana@ejemplo.cl
```

La contraseña se solicita de forma interactiva y no queda en el historial de
comandos. Después se ingresa en <http://localhost:5173> y, desde la interfaz, el
administrador puede crear las demás cuentas, los perfiles profesionales y los
pacientes.

| Servicio | URL |
|---|---|
| Frontend | <http://localhost:5173> |
| API | <http://localhost:8000> |
| Documentación OpenAPI | <http://localhost:8000/docs> |
| Salud del servicio | <http://localhost:8000/api/v1/health> |
| Salud de la base de datos | <http://localhost:8000/api/v1/health/db> |
| PostgreSQL (host) | `localhost:5433` |

Detener el entorno sin borrar datos:

```bash
docker compose down
```

`docker compose down -v` elimina la base de datos y los documentos. Es
**destructivo** y no debe ejecutarse sin autorización explícita.

## Roles y alcance

| Rol | Puede |
|---|---|
| Administrador | Gestionar usuarios, profesionales y pacientes; consultar toda la agenda y las atenciones; anotar observaciones administrativas; subir documentos y descargar cualquiera; eliminar solo los documentos que subió |
| Profesional | Gestionar su propia agenda; registrar y corregir sus atenciones; consultar pacientes y profesionales; subir documentos a sus atenciones o a un paciente; descargar lo que le corresponde; eliminar solo lo que subió |

Reglas relevantes:

- El administrador **no** crea, confirma, cancela ni registra atenciones.
- El profesional solo ve sus citas y atenciones; un recurso ajeno responde 404.
- Una atención solo se registra desde una cita confirmada y el profesional debe
  ser su dueño.
- Los pacientes con historial (citas, atenciones o documentos) no se eliminan.
- Los documentos aceptados son PDF, JPEG y PNG de hasta 10 MB, validados por el
  contenido real del archivo.
- Un documento puede existir sin atención, ligado solo al paciente. Los
  documentos sin atención subidos por el administrador no son visibles para los
  profesionales.

## Pruebas automatizadas

### Backend

```bash
docker compose exec backend pytest
```

Las pruebas de integración crean una base aparte (`citas_municipales_test`),
aplican las migraciones desde cero y la eliminan al terminar. Nunca usan la base
de desarrollo ni datos reales.

Si `DATABASE_URL` apunta a un proveedor externo (Neon), ejecute las pruebas
contra la base local para no crear bases temporales en el proveedor:

```powershell
docker compose run --rm -e DATABASE_URL="postgresql+psycopg://citas_app:CLAVE_LOCAL@db:5432/citas_municipales" backend pytest
```

Resultado de referencia al cierre: **133 passed, 1 warning**.

### Frontend

```bash
docker compose exec frontend npm audit
docker compose exec frontend npm run build
```

Resultado de referencia: **0 vulnerabilidades** y build de producción correcto.

### Pruebas de extremo a extremo (E2E)

Requieren el entorno Docker levantado y las cuentas sintéticas existentes. La
suite usa Chrome por defecto, crea un paciente de prueba, recorre el flujo
completo y elimina sus datos y archivos al terminar.

```bash
cd e2e
npm install

$env:DISS_E2E_ADMIN_PASSWORD = "clave-del-administrador"
$env:DISS_E2E_PROF_PASSWORD  = "clave-del-profesional"
npx playwright test
```

Variables disponibles:

| Variable | Valor por defecto | Uso |
|---|---|---|
| `DISS_E2E_BASE_URL` | `http://localhost:5173` | URL del frontend |
| `DISS_E2E_ADMIN_RUT` | `11111111-1` | Cuenta administradora |
| `DISS_E2E_ADMIN_PASSWORD` | — (obligatoria) | Contraseña del administrador |
| `DISS_E2E_PROF_RUT` | `12345678-5` | Cuenta profesional |
| `DISS_E2E_PROF_PASSWORD` | — (obligatoria) | Contraseña del profesional |
| `PLAYWRIGHT_CHANNEL` | `chrome` | `chrome`, `msedge` o `chromium` |
| `DISS_DB_USER` | `citas_app` | Usuario usado por la limpieza |
| `DISS_DB_NAME` | `citas_municipales` | Base usada por la limpieza |

Si no hay Chrome instalado:

```bash
npx playwright install chromium
$env:PLAYWRIGHT_CHANNEL = "chromium"
```

La suite usa el RUT sintético `77777777-7` y borra únicamente esos datos
(`documentos`, `atenciones`, `citas` y `paciente`) antes y después de ejecutar.
El informe HTML queda en `e2e/playwright-report/` (no versionado).

## Respaldo y restauración

Los respaldos incluyen la base de datos (`pg_dump` en formato custom) y el
volumen privado de documentos (`tar.gz`), más un manifiesto con sus hashes
SHA256. Se guardan en `respaldos/`, que no se versiona.

Crear un respaldo:

```powershell
.\scripts\respaldo.ps1
```

Crear un respaldo y **verificar la restauración** en una base y un directorio
temporales, comparando conteos de tablas y el contenido de los documentos:

```powershell
.\scripts\respaldo.ps1 -Verificar
```

Restaurar un respaldo sobre el entorno actual (**reemplaza** la base y los
documentos; el script detiene el backend durante la operación):

```powershell
.\scripts\restauracion.ps1 `
  -Base .\respaldos\base_20261102_120000.dump `
  -Documentos .\respaldos\documentos_20261102_120000.tar.gz `
  -Confirmar
```

Recomendaciones:

- Copiar los respaldos a otro equipo o medio; el volumen de Docker no es un
  respaldo.
- Verificar cada respaldo con `-Verificar` antes de confiar en él.
- Probar la restauración completa en un entorno separado antes de un uso real.
- Proteger los respaldos: contienen datos personales y clínicos.

## Variables de entorno

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Cadena de conexión completa. Si se define, tiene prioridad sobre la base local de Docker Compose. |
| `POSTGRES_DB` | Nombre de la base de datos local (respaldo cuando no hay `DATABASE_URL`). |
| `POSTGRES_USER` | Usuario de la base de datos local. |
| `POSTGRES_PASSWORD` | Contraseña de la base de datos local. No se versiona. |
| `SECRET_KEY` | Secreto para la firma de JWT. |
| `ENTORNO` | `desarrollo`, `pruebas` o `produccion`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Vigencia del token de acceso (480 por defecto). |
| `MAX_DOCUMENTO_MB` | Tamaño máximo permitido por documento (10 por defecto). |
| `VITE_API_URL` | URL base de la API consumida por el frontend. |
| `VITE_ALLOWED_HOSTS` | Hosts permitidos por Vite, separados por coma. Por defecto `aplicacion-discapacidad.onrender.com`. |

### Base de datos externa (Neon)

Para usar una base PostgreSQL administrada, defina `DATABASE_URL` en `.env`:

```text
DATABASE_URL=postgresql://USUARIO:CLAVE@HOST/BASE?sslmode=require
```

El backend acepta los esquemas `postgresql://`, `postgres://` y
`postgresql+psycopg://`; los dos primeros se normalizan automáticamente a
psycopg 3. Al definir `DATABASE_URL`, Docker Compose deja de usar la base local
del servicio `db` para el backend.

Aplicar migraciones y crear la cuenta administradora contra esa base:

```powershell
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.cli.crear_admin --rut 11111111-1 --nombres Ana --apellidos Administradora --correo ana@ejemplo.cl
```

El plan gratuito de Neon es permanente dentro de sus límites (1 GB por
proyecto, 100 CU-horas al mes y suspensión por inactividad). No es una prueba
de 30 días y no borra los datos al alcanzar el límite. Para datos clínicos
reales se requiere un plan con respaldos y acuerdo de tratamiento de datos.

### Nota para desplegar en Render

El contenedor del frontend ejecuta Vite en modo desarrollo. Para publicarlo:

- Defina `VITE_ALLOWED_HOSTS` con el dominio público del frontend (por ejemplo,
  `aplicacion-discapacidad.onrender.com`).
- Defina `VITE_API_URL` con la URL pública del backend; si no, el navegador
  intentará `http://localhost:8000`.
- En el backend, defina `CORS_ORIGINS` con el origen público del frontend, por
  ejemplo `["https://aplicacion-discapacidad.onrender.com"]`.
- El disco de Render es efímero: sin un disco persistente, los documentos
  subidos se pierden al reiniciar el servicio.

Generar un secreto nuevo:

```powershell
docker compose exec backend python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Estructura del proyecto

```text
aplicacion_DISS/
├─ docker-compose.yml
├─ .env.example
├─ README.md
├─ MANUAL_USUARIO.md
├─ ESTADO_PROYECTO.md
├─ backend/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  ├─ alembic.ini
│  ├─ migrations/              # Entorno de Alembic y versiones del esquema
│  ├─ tests/                   # Pruebas pytest
│  └─ app/
│     ├─ main.py               # Aplicación FastAPI
│     ├─ core/                 # Configuración, errores, RUT, seguridad y tiempo
│     ├─ api/                  # Dependencias y rutas de la API v1
│     ├─ schemas/              # Esquemas Pydantic de entrada y salida
│     ├─ services/             # Lógica de negocio
│     ├─ models/               # Modelos ORM
│     ├─ cli/                  # Comandos administrativos
│     └─ db/                   # Motor y sesiones de SQLAlchemy
├─ frontend/
│  ├─ Dockerfile
│  ├─ vite.config.js
│  └─ src/
│     ├─ api.js                # Cliente HTTP con JWT
│     ├─ auth.jsx              # Sesión y guardas de ruta
│     ├─ components/           # Layout, componentes comunes y documentos
│     └─ pages/                # Login, resumen, citas, atenciones, etc.
├─ e2e/                        # Suite Playwright versionada
│  ├─ playwright.config.js
│  ├─ limpieza.js
│  └─ pruebas/
└─ scripts/
   ├─ respaldo.ps1
   └─ restauracion.ps1
```

## Volúmenes persistentes

| Volumen | Uso |
|---|---|
| `diss_postgres_data` | Datos de PostgreSQL. |
| `diss_documentos_data` | Archivos de documentos (acceso privado, fuera de PostgreSQL). |

Los volúmenes **no sustituyen** a las copias de seguridad. Use los scripts de
respaldo y restauración descritos arriba.

## Seguridad y limitaciones

- No hay registro público ni recuperación de contraseña; un administrador debe
  crear las cuentas y asignar una contraseña inicial.
- La sesión del frontend usa `sessionStorage`: sobrevive a recargas, pero no al
  cierre de la pestaña. El token expira según `ACCESS_TOKEN_EXPIRE_MINUTES`.
- El backend aplica permisos por rol y por propietario; ocultar opciones en la
  interfaz no sustituye esos controles.
- No hay auditoría de cambios ni traza de versiones anteriores de un registro
  clínico corregido.
- No hay análisis antivirus de los archivos subidos ni política de retención.
- El MVP está preparado para ejecución local con Docker Compose; no incluye
  HTTPS, proxy inverso, alta disponibilidad ni despliegue en servidor.
- Las pruebas de concurrencia se apoyan en restricciones de la base de datos;
  no se lanzan cargas concurrentes reales.

## Advertencias

- No usar datos clínicos reales en desarrollo ni en pruebas automatizadas.
- No versionar `.env`, respaldos ni secretos.
- No ejecutar `docker compose down -v` ni `alembic downgrade` sin autorización:
  eliminan datos, archivos o esquema.
- El proyecto `aplicacion_SSEE` no debe ser modificado.
