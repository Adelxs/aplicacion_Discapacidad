# Estado del proyecto — `aplicacion_DISS`

**Fecha de corte:** 29 de octubre de 2026
**Documento de referencia:** Documento Maestro de Especificaciones v1.0
**Alcance:** Sistema Municipal de Gestión de Citas y Atenciones — MVP

> Este documento refleja únicamente lo verificado hasta la fecha de corte.
> Las Etapas 1 a 5 están completas y con la suite en verde. La Etapa 5 **aún no
> tiene commit**: sus cambios están en el árbol de trabajo.

---

## 1. Resumen ejecutivo

| Aspecto | Estado real |
|---|---|
| Entorno Docker (PostgreSQL + FastAPI + React) | Funcionando, 3 servicios arriba |
| Migración inicial aplicada | Sí (`0001_esquema_inicial`, head) |
| Etapas 1 a 5 | Completadas, probadas y verificadas |
| Etapa 5 (citas y agenda) | **Completada y verificada** (sin commit) |
| Etapas 6 a 9 | No iniciadas |
| Repositorio remoto (GitHub) | **No existe**; solo repositorio local |
| Último commit | `bbcae95` (cierre de Etapa 4) |
| Cambios de Etapa 5 en git | **Sin commit** (1 modificado + 5 nuevos) |

**Resultado de la última ejecución completa de pruebas (29-10-2026):**

```text
104 passed, 1 warning in 271.31s
```

---

## 2. Stack y entorno

| Componente | Tecnología / versión |
|---|---|
| Frontend | React 18.3.1 + Vite 6.0.7 |
| Backend | FastAPI 0.115.6, Python 3.12 |
| Base de datos | PostgreSQL 17 (contenedor) |
| ORM / migraciones | SQLAlchemy 2.0.36 + Alembic 1.14.0 |
| Seguridad | Argon2id (`argon2-cffi` 23.1.0), JWT HS256 (`PyJWT` 2.10.1) |
| Validación de correo | `email-validator` 2.2.0 |
| Zona horaria | `zoneinfo` + `tzdata` 2024.2, `America/Santiago` |
| Pruebas | pytest 8.3.4 + httpx 0.28.1 |
| Contenedores | Docker 29.8.2 + Compose v5.5.1 |

**Puertos:** frontend `5173`, API `8000`, PostgreSQL `5433` en el host
(el `5432` local está ocupado por otro PostgreSQL).

**Servicios al corte:** `diss_db` (healthy), `diss_backend` (healthy,
`uvicorn --reload` sobre `/app/app`), `diss_frontend` (up).

---

## 3. Estado por etapas

| Etapa | Estado | Evidencia de verificación |
|---|---|---|
| 1. Estructura, configuración y salud | **Completada** | 3 contenedores arriba; `/api/v1/health` y `/health/db` responden 200; CORS correcto |
| 2. Modelos ORM y migraciones | **Completada** | Migración aplicada en desarrollo y en base nueva de pruebas; `alembic check` sin diferencias; 19 pruebas de esquema en verde |
| 3. Autenticación y autorización | **Completada** | Login y `/auth/me` verificados por HTTP; 401 en casos inválidos; 403 por rol |
| 4. Usuarios, profesionales y pacientes | **Completada** | 26 pruebas propias; verificación manual por HTTP |
| 5. Citas y agenda | **Completada** | 27 pruebas propias (incluye solapamientos y transiciones); verificación manual por HTTP |
| 6. Atenciones | No iniciada | — |
| 7. Documentos | No iniciada | — |
| 8. Frontend completo | No iniciada | Solo existe la pantalla mínima de estado de la Etapa 1 |
| 9. Integración y cierre | No iniciada | — |

---

## 4. Funcionalidades implementadas y verificadas

### 4.1. Infraestructura (Etapa 1)

- `docker-compose.yml` con tres servicios, volúmenes persistentes y healthchecks.
- Volumen privado para documentos declarado (`diss_documentos_data`).
- Configuración por variables de entorno; `.env` local **no versionado**.
- Manejo uniforme de errores: `{"error": {"codigo", "mensaje", "detalle"}}`.
- CORS restringido a `http://localhost:5173`.
- Frontend mínimo que consulta `/health` y `/health/db`.

### 4.2. Base de datos (Etapa 2)

Seis tablas: `usuarios`, `profesionales`, `pacientes`, `citas`, `atenciones`,
`documentos`, más `alembic_version`.

Restricciones verificadas:

- RUT canónico (`12345678-9`) por `CHECK`.
- `fecha_hora_fin > fecha_hora_inicio`; estados de cita limitados a cinco valores.
- Una atención por cita (`UNIQUE`).
- Coherencia paciente/profesional mediante **FK compuesta** contra la cita.
- Documento asociado a una atención debe pertenecer al mismo paciente.
- **Sin solapamientos de agenda** con `EXCLUDE USING gist`, ignorando citas
  canceladas; protección válida ante concurrencia.
- Pacientes con historial no eliminables (`ON DELETE RESTRICT`).
- Cuenta vinculada a profesional debe tener el mismo RUT (`CHECK`).

### 4.3. Autenticación y autorización (Etapa 3)

- `POST /api/v1/auth/login` y `GET /api/v1/auth/me`.
- Contraseñas con **Argon2id**; JWT HS256 con expiración de 480 minutos.
- Token solo con `sub`, `rol`, `iat`, `exp`.
- Mensaje genérico para RUT inexistente, contraseña incorrecta, RUT inválido
  y cuenta desactivada; una cuenta desactivada pierde acceso de inmediato.
- `requiere_roles`, `requiere_administrador`, `requiere_profesional` con 403.
- Normalización y validación de RUT por módulo 11.
- CLI `python -m app.cli.crear_admin`.

### 4.4. Usuarios, profesionales y pacientes (Etapa 4)

| Recurso | Endpoints | Permisos |
|---|---|---|
| Usuarios | `GET`, `POST`, `GET/{rut}`, `PATCH/{rut}` | Solo administrador |
| Profesionales | `GET`, `POST`, `GET/{rut}`, `PATCH/{rut}` | Consulta: ambos roles. Alta/edición: solo administrador |
| Pacientes | `GET`, `POST`, `GET/{rut}`, `PATCH/{rut}`, `DELETE/{rut}` | Consulta: ambos roles. Alta/edición/borrado: solo administrador |

Comportamiento verificado: normalización de RUT, validación de correo con
`EmailStr`, paginación en servidor, búsqueda parcial por RUT, filtros por
`rol`/`activo`/`especialidad`, duplicados 409, vinculación de cuenta con mismo
RUT y borrado de paciente solo sin historial.

### 4.5. Citas y agenda (Etapa 5)

| Método | Ruta | Permisos |
|---|---|---|
| `GET` | `/api/v1/citas` | Administrador: todas. Profesional: solo las suyas |
| `POST` | `/api/v1/citas` | Solo profesional; agenda para sí mismo |
| `GET` | `/api/v1/citas/{id}` | Administrador o profesional dueño |
| `POST` | `/api/v1/citas/{id}/confirmar` | Solo profesional dueño |
| `POST` | `/api/v1/citas/{id}/cancelar` | Solo profesional dueño |
| `POST` | `/api/v1/citas/{id}/ausente` | Solo profesional dueño |
| `PATCH` | `/api/v1/citas/{id}/observaciones` | Solo administrador (único campo editable) |

Reglas implementadas:

- `profesional_rut`, `estado` y `creado_por_rut` **no se aceptan en el cuerpo**
  (`extra="forbid"`); se derivan de la identidad autenticada.
- El profesional debe tener un perfil profesional activo (409 si no lo tiene).
- El paciente debe existir (404) y estar activo (409).
- `fecha_hora_fin > fecha_hora_inicio` (422).
- Solapamiento con otra cita activa del mismo profesional → **409**, tanto por
  comprobación previa como por la restricción `EXCLUDE` de PostgreSQL.
- Horarios contiguos (`fin == inicio siguiente`) se permiten.
- Cancelar libera el horario.
- Transiciones: `pendiente → confirmada | cancelada`;
  `confirmada → atendida | cancelada | ausente`. Los estados terminales no
  cambian (409). `atendida` se reserva para la Etapa 6.
- Un profesional que intenta ver o modificar una cita ajena recibe **404**
  (no se revela su existencia).
- Listado con búsqueda parcial por RUT del paciente, filtro por estado, rango
  de fechas (`desde`/`hasta`, inclusivos, en hora de Santiago) y paginación.
- Fechas: un `datetime` sin zona se interpreta como hora de Santiago; con zona
  se convierte al instante correspondiente. Las respuestas se presentan con
  offset de `America/Santiago` (por ejemplo `2027-01-15T10:00:00-03:00`).

### 4.6. Verificación manual contra la API real (29-10-2026)

Ejecutada con `httpx` contra `http://localhost:8000` (uvicorn real), con datos
sintéticos y limpieza posterior:

| Comprobación | Resultado |
|---|---|
| Login de administrador y de profesional | 200 / 200 |
| Alta de paciente de prueba | 201 |
| Profesional agenda cita | 201, `profesional_rut` propio, estado `pendiente`, offset `-03:00` |
| Administrador intenta agendar | 403 `sin_permisos` |
| Solapamiento (10:15–10:45) | 409 `conflicto` |
| Cita contigua (10:30–11:00) | 201 |
| Listado: admin 2 citas; profesional 2 citas | Correcto |
| Confirmar cita | 200 |
| Marcar ausente | 200 |
| Confirmar una cita terminal | 409 `conflicto` |
| Cancelar la segunda cita | 200 |
| Administrador intenta cancelar | 403 |
| Profesional intenta editar observaciones | 403 |
| Administrador registra observaciones | 200 |
| Filtro `estado=cancelada` | 1 cita |
| Eliminación de las citas y del paciente sintéticos | Correcta (204) |

---

## 5. Historial: fallos de la Etapa 4 y su resolución

Los 13 fallos originales tenían dos causas:

1. **12 fallos: datos de prueba.** `EmailStr` rechaza dominios reservados
   `.test`; los payloads usaban `@ejemplo.test` y las altas respondían 422
   antes de la lógica de negocio. Se comprobó empíricamente y se cambiaron los
   correos a `@ejemplo.cl`, **sin relajar la validación**.
2. **1 fallo: expectativa del mensaje.** La prueba buscaba «historial» y el
   servicio decía «citas, atenciones o documentos asociados». El 409 era
   correcto; el mensaje se redactó como «El paciente tiene historial asociado
   (citas, atenciones o documentos) y no puede eliminarse» y la prueba ahora
   valida además `codigo == "conflicto"`.

Durante la verificación apareció un `pytest` huérfano de una ejecución anterior
que eliminaba `citas_municipales_test` a mitad de la suite. No afectó la base de
desarrollo; conviene comprobar que no queden procesos vivos antes de probar.

---

## 6. Pendiente de implementación

- **Etapa 6:** atenciones con transacción atómica cita + atención.
- **Etapa 7:** documentos (subida, descarga protegida, volumen privado).
- **Etapa 8:** frontend completo (login, sidebar por rol, dashboards, tablas,
  formularios, autocompletado por RUT).
- **Etapa 9:** integración, pruebas de extremo a extremo, respaldo/restauración,
  documentación final.

### Decisiones pendientes (heredadas del documento)

- Política de modificación de atenciones ya registradas.
- Flujo de cambio y recuperación de contraseña.
- Tipos y tamaños máximos de documentos.
- Definición de «actividades» del dashboard profesional.
- Política de auditoría, retención y acceso a logs.
- Filtros y campos exactos de cada tabla.
- Períodos de los indicadores del dashboard.
- Estrategia de despliegue productivo y respaldos.
- **Campos opcionales de pacientes:** `telefono`, `correo_electronico` y
  `direccion` son obligatorios (lectura literal del documento). Sin confirmar.
- **`tamano_bytes` en documentos:** columna añadida, no listada en el documento.
- **Tabla de auditoría:** no creada; necesaria para «actividad reciente».

### Decisiones tomadas para la Etapa 5

- Solo el profesional dueño confirma, cancela o marca ausencia; el
  administrador únicamente consulta y anota observaciones.
- Cambios de estado mediante endpoints dedicados (`/confirmar`, `/cancelar`,
  `/ausente`), no un `PATCH` genérico.
- El administrador solo puede editar `observaciones_administrativas`.

---

## 7. Lo que NO se ha probado

- No hay pruebas de extremo a extremo desde el navegador.
- El frontend no consume ninguno de los endpoints de negocio.
- No se ha probado la persistencia de documentos (el volumen existe, pero no
  hay módulo).
- No se ha probado respaldo ni restauración de la base de datos.
- **Concurrencia real:** la prueba desactiva la comprobación previa para forzar
  la restricción `EXCLUDE`, pero no se han lanzado dos peticiones HTTP
  simultáneas contra el servidor.
- No se ha probado el flujo de recuperación de contraseña (no existe).
- No se ha probado en un entorno distinto de este equipo Windows con Docker
  Desktop.

---

## 8. Archivos del proyecto

### 8.1. Versionados (commits `e45174f`, `9b34f82`, `81031b3`, `bbcae95`)

```text
.env.example
.gitattributes
.gitignore
README.md
docker-compose.yml
ESTADO_PROYECTO.md
backend/
  .dockerignore                 Dockerfile
  requirements.txt              requirements-dev.txt
  alembic.ini                   pytest.ini
  app/
    __init__.py                 main.py
    core/{__init__,config,errors,rut,security}.py
    db/{__init__,base,session}.py
    models/{__init__,enums,usuario,profesional,paciente,cita,atencion,documento}.py
    schemas/{__init__,auth,common,usuario,profesional,paciente}.py
    api/{__init__,comun,deps}.py
    api/v1/{__init__,router,health,auth,usuarios,profesionales,pacientes}.py
    services/{__init__,paginacion,usuarios,profesionales,pacientes}.py
    cli/{__init__,crear_admin}.py
  migrations/
    env.py                      script.py.mako
    versions/0001_esquema_inicial.py
  tests/{__init__,conftest,apoyo,test_esquema,test_rut,test_auth,test_etapa4}.py
frontend/
  .dockerignore                 Dockerfile
  index.html                    package.json
  vite.config.js
  src/{main.jsx,App.jsx,index.css}
```

### 8.2. Sin commit (Etapa 5)

```text
Modificados:
  backend/app/api/v1/router.py          # registra el router de citas

Nuevos:
  backend/app/core/tiempo.py            # zona America/Santiago
  backend/app/schemas/cita.py
  backend/app/services/citas.py
  backend/app/api/v1/citas.py
  backend/tests/test_etapa5.py
```

### 8.3. Solo local (no versionado)

```text
.env                        # credenciales locales generadas
```

---

## 9. Base de datos de desarrollo al corte

| Tabla | Filas |
|---|---|
| usuarios | 2 |
| profesionales | 1 |
| pacientes | 0 |
| citas | 0 |
| atenciones | 0 |
| documentos | 0 |

- `11111111-1`: cuenta administradora local creada con el CLI. Su contraseña se
  comunicó en la sesión y **no se guarda en este documento ni en el repositorio**.
- `12345678-5`: usuario profesional sintético con su perfil vinculado, creado en
  la verificación de la Etapa 4. Su contraseña es la de los datos de prueba.

Las citas y el paciente usados en la verificación de la Etapa 5 se eliminaron
al terminar. No hay datos clínicos reales.

---

## 10. Comandos de operación

```bash
docker compose up -d --build

docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
docker compose exec backend alembic check

docker compose exec backend pytest
docker compose exec backend pytest tests/test_etapa5.py -v

docker compose exec backend python -m app.cli.crear_admin \
  --rut 11111111-1 --nombres Ana --apellidos Administradora \
  --correo ana@ejemplo.cl
```

- Frontend: <http://localhost:5173>
- Swagger: <http://localhost:8000/docs>
- Salud: <http://localhost:8000/api/v1/health>

Las pruebas crean y eliminan `citas_municipales_test`; nunca tocan la base de
desarrollo. Si una ejecución se interrumpe, puede quedar un `pytest` huérfano
que elimine esa base a mitad de la siguiente ejecución.

---

## 11. Cierre de la Etapa 5

| Criterio | Estado |
|---|---|
| 1. El profesional agenda solo para sí mismo; el RUT sale de la identidad | Cumplido (`extra="forbid"` + servicio) |
| 2. El administrador consulta pero no crea, modifica ni cancela | Cumplido (403 verificado) |
| 3. Se rechaza `fin <= inicio` | Cumplido (422) |
| 4. Solapamiento activo → 409 | Cumplido (prueba y HTTP) |
| 5. Una cita cancelada no bloquea el horario | Cumplido |
| 6. Transiciones permitidas y terminales inmutables | Cumplido |
| 7. Endpoints de cancelación y ausencia actualizan estado | Cumplido |
| 8. Un profesional no ve ni modifica citas ajenas | Cumplido (404) |
| 9. Búsqueda por RUT, filtro por estado y rango, paginación | Cumplido |
| 10. Pruebas de permisos, solapamientos, transiciones y concurrencia | Cumplido salvo concurrencia HTTP real (ver sección 7) |
| 11. Fechas en `America/Santiago`, almacenadas con zona | Cumplido |
| Commit de la etapa | **Pendiente de autorización** |

`alembic check` responde «No new upgrade operations detected»: la Etapa 5 no
introdujo cambios de esquema.

---

## 12. Siguiente etapa propuesta: Etapa 6 — Atenciones

**Objetivo:** registrar la atención clínica de una cita confirmada en una sola
transacción, de modo que no exista cita atendida sin atención ni atención sin
cita.

**Puntos a definir antes de implementar:**

1. Campos editables después del registro y quién puede corregirlos.
2. Contenido mínimo del registro clínico y su longitud máxima.
3. Confirmación explícita de que solo el profesional dueño registra la
   atención, y que la cita debe estar en estado `confirmada`.
4. Relación con documentos (Etapa 7): la atención podrá recibir documentos
   asociados al mismo paciente.

**Requisito previo:** cerrado; la Etapa 5 está en verde y solo falta el commit.

---

## 13. Registro de verificaciones ejecutadas

| Fecha | Verificación | Resultado |
|---|---|---|
| 27-10-2026 | `docker compose up` y healthchecks | 3 servicios healthy |
| 27-10-2026 | `GET /api/v1/health` y `/health/db` | 200 |
| 27-10-2026 | `alembic upgrade head` y `alembic check` | OK / sin diferencias |
| 27-10-2026 | `pytest` al cierre de Etapa 2 | 19 passed |
| 27-10-2026 | `pytest` al cierre de Etapa 3 | 51 passed |
| 28-10-2026 | `pytest` con Etapa 4 (diagnóstico) | 13 failed, 64 passed |
| 28-10-2026 | Dominios aceptados por `email-validator` 2.2.0 | `.test` rechazado; `.cl`/`.com`/`.org` aceptados |
| 28-10-2026 | `pytest tests/test_etapa4.py` | 26 passed |
| 28-10-2026 | `pytest` (suite completa) | **77 passed** |
| 28-10-2026 | Verificación manual por HTTP de la Etapa 4 | 13 comprobaciones correctas |
| 29-10-2026 | `pytest tests/test_etapa5.py` | 27 passed |
| 29-10-2026 | `pytest` (suite completa) | **104 passed**, 1 warning |
| 29-10-2026 | `alembic check` tras la Etapa 5 | «No new upgrade operations detected» |
| 29-10-2026 | Verificación manual por HTTP de la Etapa 5 | 16 comprobaciones correctas (sección 4.6) |

---

## 14. Notas y advertencias

- El contenedor `diss_backend` ejecuta el código del árbol de trabajo mediante
  `uvicorn --reload`, aunque git HEAD no tenga la Etapa 5.
- No hay repositorio remoto ni nada publicado en GitHub.
- El proyecto `aplicacion_SSEE` no ha sido modificado ni consultado.
- No se usan datos clínicos reales; todos los datos de prueba son sintéticos.
- No se deben ejecutar `docker compose down -v` ni `alembic downgrade` sin
  autorización: eliminan datos y esquema.
