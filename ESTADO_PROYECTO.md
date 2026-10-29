# Estado del proyecto — `aplicacion_DISS`

**Fecha de corte:** 29 de octubre de 2026
**Documento de referencia:** Documento Maestro de Especificaciones v1.0
**Alcance:** Sistema Municipal de Gestión de Citas y Atenciones — MVP

> Este documento refleja únicamente lo verificado hasta la fecha de corte.
> Las Etapas 1 a 6 están completas y con la suite en verde. La Etapa 6 **aún no
> tiene commit**: sus cambios están en el árbol de trabajo.

---

## 1. Resumen ejecutivo

| Aspecto | Estado real |
|---|---|
| Entorno Docker (PostgreSQL + FastAPI + React) | Funcionando, 3 servicios arriba |
| Migración inicial aplicada | Sí (`0001_esquema_inicial`, head) |
| Etapas 1 a 6 | Completadas, probadas y verificadas |
| Etapa 6 (atenciones) | **Completada y verificada** (sin commit) |
| Etapas 7 a 9 | No iniciadas |
| Repositorio remoto (GitHub) | **No existe**; solo repositorio local |
| Último commit | `9ee42e3` (cierre de Etapa 5) |
| Cambios de Etapa 6 en git | **Sin commit** (2 modificados + 4 nuevos) |

**Resultado de la última ejecución completa de pruebas (29-10-2026):**

```text
119 passed, 1 warning in 445.60s
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

---

## 3. Estado por etapas

| Etapa | Estado | Evidencia de verificación |
|---|---|---|
| 1. Estructura, configuración y salud | **Completada** | 3 contenedores; `/api/v1/health` y `/health/db` 200; CORS |
| 2. Modelos ORM y migraciones | **Completada** | Migración aplicada; `alembic check` limpio; 19 pruebas de esquema |
| 3. Autenticación y autorización | **Completada** | Login y `/auth/me` por HTTP; 401 y 403 verificados |
| 4. Usuarios, profesionales y pacientes | **Completada** | 26 pruebas propias; verificación manual por HTTP |
| 5. Citas y agenda | **Completada** | 27 pruebas propias; verificación manual por HTTP |
| 6. Atenciones | **Completada** | 15 pruebas propias; verificación manual por HTTP |
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

Reglas: `profesional_rut`, `estado` y `creado_por_rut` no se aceptan en el
cuerpo; el profesional debe tener perfil activo; el paciente debe existir y
estar activo; `fin > inicio`; solapamiento → 409 (comprobación previa +
`EXCLUDE`); horarios contiguos permitidos; cancelar libera el horario;
transiciones `pendiente → confirmada | cancelada` y
`confirmada → atendida | cancelada | ausente`, terminales inmutables; cita
ajena → 404; filtros por RUT de paciente, estado y rango de fechas; fechas en
`America/Santiago`.

### 4.6. Atenciones (Etapa 6)

| Método | Ruta | Permisos |
|---|---|---|
| `GET` | `/api/v1/atenciones` | Administrador: todas. Profesional: solo las suyas |
| `POST` | `/api/v1/atenciones` | Solo el profesional dueño de la cita |
| `GET` | `/api/v1/atenciones/{id}` | Administrador o profesional dueño |
| `PATCH` | `/api/v1/atenciones/{id}` | Solo el profesional que la registró |

Reglas implementadas:

- Solo se registra sobre una cita en estado **`confirmada`**; en la misma
  transacción la cita pasa a **`atendida`**. Si el registro falla, la cita no
  cambia de estado (atomicidad).
- Una cita admite **una sola** atención: segunda inserción → 409.
- `paciente_rut`, `profesional_rut` y `creado_por_rut` no se aceptan en el
  cuerpo: se derivan de la cita y de la identidad autenticada.
- La `fecha_atencion` la envía el profesional y debe caer dentro del horario de
  la cita (`inicio <= fecha <= fin`); fuera de rango → 422.
- El profesional que registró la atención puede corregir `motivo` y
  `registro_clinico`; no puede cambiarla de cita ni de paciente.
- El administrador solo consulta (403 al intentar registrar o corregir).
- Atención de otro profesional → 404.
- Listado con búsqueda parcial por RUT del paciente, rango de fechas y
  paginación; orden descendente por fecha de atención.
- Fechas presentadas en `America/Santiago`.

### 4.7. Verificación manual de la Etapa 5 (29-10-2026)

16 comprobaciones por HTTP real (uvicorn, no `TestClient`): agenda del
profesional (201, `profesional_rut` propio, estado `pendiente`, offset
`-03:00`), 403 del administrador al crear, solapamiento 409, cita contigua 201,
listados por rol, confirmar/ausente, terminal 409, cancelar, 403 del
administrador al cancelar, 403 del profesional al editar observaciones, 200 del
administrador, filtro por estado y limpieza de los datos sintéticos.

### 4.8. Verificación manual de la Etapa 6 (29-10-2026)

Ejecutada con `httpx` contra la API real y datos sintéticos eliminados al final:

| Comprobación | Resultado |
|---|---|
| Atención sobre cita pendiente | 409 (`conflicto`) |
| Confirmar cita | 200 |
| Registrar atención | 201, `fecha_atencion` `2027-01-15T10:05:00-03:00` |
| Segunda atención sobre la misma cita | 409 |
| Administrador intenta registrar | 403 |
| Estado de la cita tras la atención | `atendida` |
| Profesional corrige su atención | 200 |
| Listados: admin y profesional ven 1 | Correcto |
| Filtro por RUT del paciente | 1 atención |
| Fecha fuera del horario de la cita | 422 (`datos_invalidos`) |
| Limpieza de atenciones, citas y paciente | Correcta |

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

- **Etapa 7:** documentos (subida, descarga protegida, volumen privado).
- **Etapa 8:** frontend completo (login, sidebar por rol, dashboards, tablas,
  formularios, autocompletado por RUT).
- **Etapa 9:** integración, pruebas de extremo a extremo, respaldo/restauración,
  documentación final.

### Decisiones pendientes (heredadas del documento)

- Flujo de cambio y recuperación de contraseña.
- Definición de «actividades» del dashboard profesional.
- Política de auditoría, retención y acceso a logs.
- Filtros y campos exactos de cada tabla.
- Períodos de los indicadores del dashboard.
- Estrategia de despliegue productivo y respaldos.
- **Campos opcionales de pacientes:** `telefono`, `correo_electronico` y
  `direccion` son obligatorios (lectura literal del documento). Sin confirmar.
- **`tamano_bytes` en documentos:** columna añadida, no listada en el documento.
- **Tabla de auditoría:** no creada; necesaria para «actividad reciente».
- **Corrección de atenciones:** el profesional dueño puede editar `motivo` y
  `registro_clinico`; no queda traza de la versión anterior hasta que exista
  auditoría.

### Decisiones tomadas para las Etapas 5 y 6

- Solo el profesional dueño confirma, cancela o marca ausencia; el
  administrador únicamente consulta y anota observaciones.
- Cambios de estado de citas mediante endpoints dedicados.
- La atención solo se registra desde una cita confirmada, por el profesional
  dueño, con fecha enviada y validada dentro del horario.
- La atención se puede corregir después por quien la registró.
- El administrador nunca escribe datos clínicos.

---

## 7. Lo que NO se ha probado

- No hay pruebas de extremo a extremo desde el navegador.
- El frontend no consume ninguno de los endpoints de negocio.
- No se ha probado la persistencia de documentos (el volumen existe, pero no
  hay módulo).
- No se ha probado respaldo ni restauración de la base de datos.
- **Concurrencia real:** las pruebas fuerzan las restricciones de la base
  (solapamiento y atención única) sin lanzar dos peticiones HTTP simultáneas.
- No se ha probado el flujo de recuperación de contraseña (no existe).
- No se ha probado en un entorno distinto de este equipo Windows con Docker
  Desktop.

---

## 8. Archivos del proyecto

### 8.1. Versionados (commits `e45174f`, `9b34f82`, `81031b3`, `bbcae95`, `9ee42e3`)

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
    core/{__init__,config,errors,rut,security,tiempo}.py
    db/{__init__,base,session}.py
    models/{__init__,enums,usuario,profesional,paciente,cita,atencion,documento}.py
    schemas/{__init__,auth,common,usuario,profesional,paciente,cita}.py
    api/{__init__,comun,deps}.py
    api/v1/{__init__,router,health,auth,usuarios,profesionales,pacientes,citas}.py
    services/{__init__,paginacion,usuarios,profesionales,pacientes,citas}.py
    cli/{__init__,crear_admin}.py
  migrations/
    env.py                      script.py.mako
    versions/0001_esquema_inicial.py
  tests/{__init__,conftest,apoyo,test_esquema,test_rut,test_auth,test_etapa4,
         test_etapa5}.py
frontend/
  .dockerignore                 Dockerfile
  index.html                    package.json
  vite.config.js
  src/{main.jsx,App.jsx,index.css}
```

### 8.2. Sin commit (Etapa 6)

```text
Modificados:
  backend/app/api/v1/router.py          # registra el router de atenciones
  backend/tests/conftest.py             # fixture crear_atencion acepta autor

Nuevos:
  backend/app/schemas/atencion.py
  backend/app/services/atenciones.py
  backend/app/api/v1/atenciones.py
  backend/tests/test_etapa6.py
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

Todas las citas, atenciones y pacientes usados en las verificaciones se
eliminaron al terminar. No hay datos clínicos reales.

---

## 10. Comandos de operación

```bash
docker compose up -d --build

docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
docker compose exec backend alembic check

docker compose exec backend pytest
docker compose exec backend pytest tests/test_etapa6.py -v

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

## 11. Cierre de las Etapas 5 y 6

### Etapa 5 — Citas y agenda

| Criterio | Estado |
|---|---|
| Profesional agenda solo para sí mismo | Cumplido |
| Administrador solo consulta | Cumplido (403) |
| `fin <= inicio` rechazado | Cumplido (422) |
| Solapamiento activo rechazado | Cumplido (409) |
| Cita cancelada libera el horario | Cumplido |
| Transiciones y terminales | Cumplido |
| Endpoints de cancelación y ausencia | Cumplido |
| Cita ajena invisible | Cumplido (404) |
| Filtros y paginación | Cumplido |
| Pruebas de permisos, solapamientos y transiciones | Cumplido |
| Fechas en `America/Santiago` | Cumplido |

### Etapa 6 — Atenciones

| Criterio | Estado |
|---|---|
| Solo el profesional dueño registra | Cumplido |
| Solo desde cita confirmada | Cumplido (409 en otros estados) |
| Transición atómica a `atendida` | Cumplido (rollback verificado) |
| Una atención por cita | Cumplido (409) |
| Fecha enviada y validada en el horario | Cumplido (422 fuera de rango) |
| Corrección por el profesional que la registró | Cumplido |
| Administrador sin escritura clínica | Cumplido (403) |
| Atención ajena invisible | Cumplido (404) |
| Listados, filtros y paginación | Cumplido |
| Commit de la etapa | **Pendiente de autorización** |

`alembic check` responde «No new upgrade operations detected»: las Etapas 5 y 6
no introdujeron cambios de esquema.

---

## 12. Siguiente etapa propuesta: Etapa 7 — Documentos

**Objetivo:** adjuntar archivos privados a un paciente (y opcionalmente a una
atención), almacenados fuera de la base de datos y servidos solo a usuarios
autorizados.

El modelo ya existe: `id_documento`, `paciente_rut`, `id_atencion` (opcional),
`nombre_original`, `tipo_mime`, `tamano_bytes`, `clave_archivo` (única),
`subido_por_rut`, `fecha_creacion`; con coherencia paciente/atención y el
volumen `diss_documentos_data` declarado.

**Decisiones a consultar antes de implementar:**

1. Quién puede subir: ¿solo el profesional dueño de la atención, también el
   administrador, o ambos?
2. Quién puede descargar: ¿administrador y profesional dueño, o todo
   profesional autenticado?
3. Tipos MIME permitidos (por ejemplo PDF, imágenes) y tamaño máximo.
4. Si se permite borrar documentos y con qué permisos.
5. Si un documento puede existir sin atención (`id_atencion` nulo).

**Requisito previo:** cerrado salvo el commit de la Etapa 6.

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
| 29-10-2026 | `pytest` (suite completa) | **104 passed** |
| 29-10-2026 | Verificación manual por HTTP de la Etapa 5 | 16 comprobaciones correctas |
| 29-10-2026 | `pytest tests/test_etapa6.py` | 15 passed |
| 29-10-2026 | `pytest` (suite completa) | **119 passed**, 1 warning |
| 29-10-2026 | `alembic check` tras la Etapa 6 | «No new upgrade operations detected» |
| 29-10-2026 | Verificación manual por HTTP de la Etapa 6 | 11 comprobaciones correctas (sección 4.8) |

---

## 14. Notas y advertencias

- El contenedor `diss_backend` ejecuta el código del árbol de trabajo mediante
  `uvicorn --reload`, aunque git HEAD no tenga la Etapa 6.
- No hay repositorio remoto ni nada publicado en GitHub.
- El proyecto `aplicacion_SSEE` no ha sido modificado ni consultado.
- No se usan datos clínicos reales; todos los datos de prueba son sintéticos.
- No se deben ejecutar `docker compose down -v` ni `alembic downgrade` sin
  autorización: eliminan datos y esquema.
- Las correcciones de atenciones no dejan traza hasta que exista auditoría.
