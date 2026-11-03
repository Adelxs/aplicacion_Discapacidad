# Estado del proyecto — `aplicacion_DISS`

**Fecha de corte:** 3 de noviembre de 2026
**Documento de referencia:** Documento Maestro de Especificaciones v1.0
**Alcance:** Sistema Municipal de Gestión de Citas y Atenciones — MVP

> Este documento refleja únicamente lo verificado hasta la fecha de corte.
> Las Etapas 1 a 9 están completas, verificadas y con commit.

---

## 1. Resumen ejecutivo

| Aspecto | Estado real |
|---|---|
| Entorno Docker (PostgreSQL + FastAPI + React) | Funcionando, 3 servicios arriba |
| Base de datos externa | **Neon Free conectada**; migración `0001_esquema_inicial` aplicada |
| Migración inicial aplicada | Sí (`0001_esquema_inicial`, head) |
| Etapas 1 a 9 | Completadas, probadas y verificadas |
| Etapa 7 (documentos) | **Completada y verificada** (commit `a732633`) |
| Etapa 8 (frontend) | **Completada y verificada en navegador** (commit de cierre de la Etapa 8) |
| Etapa 9 (cierre) | **Completada**: suite E2E versionada, respaldo verificado y documentación final |
| Repositorio remoto (GitHub) | **Publicado**: <https://github.com/Adelxs/aplicacion_Discapacidad> |
| Último commit | Conexión del backend a Neon y documentación (03-11-2026) |
| Cambios de Etapa 9 en git | **Commiteados**; árbol de trabajo limpio |

**Resultado de la última ejecución completa de pruebas del backend (02-11-2026):**

```text
133 passed, 1 warning in 539.56s
```

**Verificación del frontend (02-11-2026):** build de producción correcto,
`npm audit` con **0 vulnerabilidades** y flujo de extremo a extremo en Chrome
headless sin errores de consola.

**Cierre de la Etapa 9 (02-11-2026):** suite Playwright versionada en `e2e/`
(1 prueba, 7 pasos, resultado `1 passed`), respaldo con `pg_dump` + `tar.gz` +
manifiesto SHA256 verificado restaurando en base y directorio temporales
(conteos `2,1,0,0,0,0,1` y contenido de documentos idéntico), scripts
`respaldo.ps1` y `restauracion.ps1` con sintaxis validada, y documentación final
en `README.md` y `MANUAL_USUARIO.md`. La restauración real **no se ejecutó sobre
los datos de desarrollo**.

---

## 2. Stack y entorno

| Componente | Tecnología / versión |
|---|---|
| Frontend | React 18.3.1 + Vite 6.4.5 + React Router 7.18.5 (CSS propio) |
| Backend | FastAPI 0.115.6, Python 3.12 |
| Base de datos | PostgreSQL 17 (contenedor) |
| ORM / migraciones | SQLAlchemy 2.0.36 + Alembic 1.14.0 |
| Seguridad | Argon2id (`argon2-cffi` 23.1.0), JWT HS256 (`PyJWT` 2.10.1) |
| Validación de correo | `email-validator` 2.2.0 |
| Subida de archivos | `python-multipart` 0.0.20 |
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
| 7. Documentos | **Completada** | 14 pruebas propias; verificación manual por HTTP y volumen |
| 8. Frontend completo | **Completada** | Build 0 vulnerabilidades; flujo E2E en Chrome headless (sección 4.11) |
| 9. Integración y cierre | **Completada** | Suite E2E `1 passed`; respaldo `-Verificar` con conteos y documentos idénticos; documentación final (sección 4.12) |

---

## 4. Funcionalidades implementadas y verificadas

### 4.1. Infraestructura (Etapa 1)

- `docker-compose.yml` con tres servicios, volúmenes persistentes y healthchecks.
- Volumen privado para documentos (`diss_documentos_data`) montado en
  `/data/documentos` del backend.
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

### 4.7. Documentos privados (Etapa 7)

| Método | Ruta | Permisos |
|---|---|---|
| `GET` | `/api/v1/documentos` | Administrador: todos. Profesional: los que subió o los de sus atenciones |
| `POST` | `/api/v1/documentos` | Profesional dueño de la atención o administrador |
| `GET` | `/api/v1/documentos/{id}` | Administrador o profesional con visibilidad |
| `GET` | `/api/v1/documentos/{id}/archivo` | Administrador o profesional con visibilidad |
| `DELETE` | `/api/v1/documentos/{id}` | Solo quien subió el documento |

La subida es `multipart/form-data` con `paciente_rut` (obligatorio),
`archivo` (obligatorio) e `id_atencion` (opcional). Reglas implementadas:

- Se aceptan **PDF, JPEG y PNG**; el tipo se determina por la **firma del
  contenido** (primeros bytes), no por el `Content-Type` ni por la extensión
  declarada. Otro contenido → **415**.
- Tamaño máximo **10 MB** por archivo (`MAX_DOCUMENTO_MB`); al excederlo →
  **413** y el archivo parcial se elimina.
- El archivo se guarda fuera de la base de datos, en el volumen privado, con un
  nombre **generado por el servidor** (UUID + extensión coherente con el
  contenido). El nombre original se sanea (`Path.name`, sin rutas ni `..`) y
  solo se conserva como metadato; `clave_archivo` no se expone en la API.
- Un documento puede existir **sin atención**, ligado al paciente (por ejemplo,
  exámenes previos). Si se indica `id_atencion`, la atención debe pertenecer al
  paciente indicado (422 si no coincide) y el profesional debe ser su dueño
  (404 en caso contrario); el administrador puede adjuntar a cualquier atención.
- Visibilidad: el administrador ve y descarga todo; el profesional ve los
  documentos que subió y los de sus propias atenciones. Un documento sin
  atención subido por el administrador **no** es visible para profesionales
  (404). El listado aplica la misma regla.
- El borrado solo lo puede hacer **quien subió** el documento; el archivo físico
  se elimina junto con el registro. El administrador que no lo subió recibe
  **403**; un profesional sin visibilidad recibe **404**.
- Listado con búsqueda parcial por RUT del paciente y paginación; orden
  descendente por fecha de creación.
- Fechas presentadas en `America/Santiago`.

### 4.8. Verificación manual de la Etapa 5 (29-10-2026)

16 comprobaciones por HTTP real (uvicorn, no `TestClient`): agenda del
profesional (201, `profesional_rut` propio, estado `pendiente`, offset
`-03:00`), 403 del administrador al crear, solapamiento 409, cita contigua 201,
listados por rol, confirmar/ausente, terminal 409, cancelar, 403 del
administrador al cancelar, 403 del profesional al editar observaciones, 200 del
administrador, filtro por estado y limpieza de los datos sintéticos.

### 4.9. Verificación manual de la Etapa 6 (29-10-2026)

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

### 4.10. Verificación manual de la Etapa 7 (29-10-2026)

Ejecutada con `httpx` contra la API real (uvicorn en Docker), con archivos y
datos sintéticos eliminados al final:

| Comprobación | Resultado |
|---|---|
| Profesional sube PDF a su atención | 201 (52 bytes, `informe.pdf`) |
| Descarga del documento | 200; bytes idénticos; `application/pdf`; `attachment; filename="informe.pdf"` |
| Administrador sube PNG del paciente sin atención | 201 |
| Profesional consulta el documento administrativo | 404 (`no_encontrado`) |
| Tipo no permitido (`text/plain`) | 415 (`tipo_no_permitido`) |
| PDF de 11 MB | 413 (`archivo_demasiado_grande`) |
| Volumen antes / durante / después | `[]` / 2 archivos / `[]` |
| Profesional elimina su documento | 204 |
| Documento eliminado ya no existe | 404 |
| Administrador elimina el suyo | 204 |
| Limpieza de atención, cita y paciente | Correcta |

El volumen `diss_documentos_data` quedó **sin archivos residuales** y la base de
desarrollo conserva solo las cuentas sintéticas habituales.

### 4.11. Frontend completo (Etapa 8)

Aplicación React con React Router 7, sesión en `sessionStorage` y cliente HTTP
propio sobre `fetch`:

- **Sesión:** login contra `/api/v1/auth/login`; el token se guarda en
  `sessionStorage` y se adjunta como `Bearer` en cada petición. Un **401** cierra
  la sesión y redirige a `/login`; las rutas privadas exigen sesión y `/usuarios`
  exige rol administrador (la navegación oculta el módulo a profesionales).
- **Pantallas:** login, resumen (dashboard), citas, atenciones, pacientes,
  profesionales, documentos y usuarios. Todas consumen los endpoints ya
  existentes; no se agregaron endpoints nuevos.
- **Dashboard:** contadores calculados con la API actual —total de citas y
  desglose por estado, atenciones, pacientes, profesionales, documentos y
  usuarios (solo administrador)—. Citas, atenciones y documentos respetan el
  filtrado por propietario del backend; pacientes y profesionales son totales
  del sistema, porque la API los expone a ambos roles.
- **Citas:** filtros por paciente, estado y rango de fechas; alta con
  autocompletado de paciente por RUT; confirmar, cancelar y marcar ausente para
  el profesional dueño; registro de la atención desde la cita confirmada; el
  administrador consulta y edita observaciones administrativas.
- **Atenciones:** listado con filtros, ficha con registro clínico, corrección por
  el profesional que la registró y documentos adjuntos de la atención.
- **Pacientes y profesionales:** tablas con filtros y paginación; alta y edición
  solo para el administrador; el profesional consulta. El borrado de pacientes
  muestra el conflicto 409 cuando existe historial.
- **Documentos:** subida desde una atención o solo con el paciente, descarga
  autenticada (blob con el nombre original), borrado únicamente por quien subió
  y listado filtrado por la visibilidad que aplica el backend.
- **UX:** mensajes de error uniformes a partir de `{"error": {...}}`, avisos de
  éxito, modales con cierre por `Escape`, paginación y formato de fechas en
  `America/Santiago`.
- **Dependencias:** `react-router-dom@7.18.5`, `vite@6.4.5` y
  `package-lock.json` versionado. `npm audit` → **0 vulnerabilidades**.

Verificación de extremo a extremo (02-11-2026, Chrome headless con
`playwright-core`, datos sintéticos eliminados al final):

| Comprobación | Resultado |
|---|---|
| Acceso sin sesión a `/` | Redirige a `/login` |
| Login del administrador y carga del dashboard | Correcto |
| Alta de paciente desde el formulario | 201 y fila visible |
| Login del profesional | Correcto |
| Profesional abre `/usuarios` | Redirige a `/`; sin enlace en el menú |
| Crear cita con autocompletado por RUT | Pendiente y visible |
| Confirmar cita y registrar atención | Correcto; cita `atendida` |
| Recarga de la página | La sesión se conserva (`sessionStorage`) |
| Subir PDF a la atención y descargarlo | Bytes idénticos, nombre original |
| Eliminar el documento como autor | Correcto |
| Sesión admin y borrado de paciente con historial | 409 mostrado en pantalla |
| Consola del navegador | Sin excepciones ni errores 5xx |

El volumen de documentos quedó vacío y la base de desarrollo sin datos E2E. Las
capturas de la verificación se conservan fuera del repositorio, en
`%TEMP%\opencode\frontend-verif`.

### 4.12. Integración y cierre (Etapa 9)

**Suite E2E versionada** en `e2e/` con `@playwright/test` 1.64.1:

- Configuración en `e2e/playwright.config.js`: Chrome del sistema por defecto
  (`PLAYWRIGHT_CHANNEL` permite `msedge` o `chromium`), `baseURL`
  `http://localhost:5173`, un worker y traza/captura solo en fallos.
- Un único recorrido serial en `e2e/pruebas/flujo-completo.spec.js` con 7 pasos:
  acceso sin sesión y login del administrador; alta de paciente; bloqueo de
  `/usuarios` para el profesional; creación, confirmación y registro de una
  cita; persistencia de la sesión al recargar; subida, descarga con bytes
  idénticos y borrado de un documento; y conflicto 409 al intentar borrar un
  paciente con historial.
- `e2e/limpieza.js` elimina, antes y después de la prueba, las filas del RUT
  sintético `77777777-7` (`documentos`, `atenciones`, `citas` y `pacientes`) y
  los archivos físicos asociados en `/data/documentos`. Solo toca ese RUT.
- Las contraseñas se pasan por `DISS_E2E_ADMIN_PASSWORD` y
  `DISS_E2E_PROF_PASSWORD`; no están en el repositorio.

| Verificación (02-11-2026) | Resultado |
|---|---|
| Suite E2E completa con la limpieza reforzada | `1 passed (1.2m)` |
| Filas del RUT de prueba tras la ejecución | 0 en las cuatro tablas |
| Volumen `/data/documentos` tras la ejecución | 0 archivos |
| Base de desarrollo | 2 usuarios, 1 profesional, 0 registros clínicos |

**Respaldo y restauración** (`scripts/respaldo.ps1` y
`scripts/restauracion.ps1`):

- El respaldo genera un `pg_dump` en formato custom, un `tar.gz` del volumen de
  documentos y un manifiesto con fecha y hashes SHA256 de ambos archivos.
- `-Verificar` restaura la base en una base temporal y los documentos en un
  directorio temporal, compara los conteos de las siete tablas (incluida
  `alembic_version`) y el hash del contenido de los documentos; luego elimina
  todo lo temporal.
- La restauración real reemplaza base y documentos, detiene el backend durante
  la operación, exige `-Confirmar` y espera a que `/api/v1/health` responda.
- Se validó la sintaxis de ambos scripts y que `restauracion.ps1` sin
  `-Confirmar` termina con código 1 sin tocar datos.

| Verificación del respaldo (02-11-2026) | Resultado |
|---|---|
| `respaldo.ps1 -Verificar` con el volumen vacío | Conteos `2,1,0,0,0,0,1`; 0 documentos |
| `respaldo.ps1 -Verificar` con un documento sintético | Conteos idénticos; 1 documento con contenido idéntico |
| Base y directorios temporales | Eliminados al terminar |
| `restauracion.ps1` sin `-Confirmar` | Cancela con código 1 |

**Documentación final:** `README.md` reescrito con puesta en marcha, roles,
pruebas, respaldo/restauración, variables y limitaciones; `MANUAL_USUARIO.md`
con el uso por rol. El alcance de despliegue queda en local con Docker Compose.

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

La Etapa 9 cerró el alcance del MVP. No quedan etapas de implementación
pendientes; los puntos siguientes son decisiones de producto o mejoras fuera
del alcance actual.

### Decisiones pendientes (heredadas del documento)

- Flujo de cambio y recuperación de contraseña.
- Definición de «actividades» del dashboard profesional (hoy son contadores de
  citas, atenciones y documentos, sin línea de actividad reciente).
- Política de auditoría, retención y acceso a logs.
- Períodos de los indicadores del dashboard (hoy son totales históricos).
- Estrategia de despliegue productivo y respaldos.
- **Campos opcionales de pacientes:** `telefono`, `correo_electronico` y
  `direccion` son obligatorios (lectura literal del documento). Sin confirmar.
- **`tamano_bytes` en documentos:** columna añadida, no listada en el documento.
- **Tabla de auditoría:** no creada; necesaria para «actividad reciente».
- **Corrección de atenciones:** el profesional dueño puede editar `motivo` y
  `registro_clinico`; no queda traza de la versión anterior hasta que exista
  auditoría.

### Decisiones tomadas para las Etapas 5, 6 y 7

- Solo el profesional dueño confirma, cancela o marca ausencia; el
  administrador únicamente consulta y anota observaciones.
- Cambios de estado de citas mediante endpoints dedicados.
- La atención solo se registra desde una cita confirmada, por el profesional
  dueño, con fecha enviada y validada dentro del horario.
- La atención se puede corregir después por quien la registró.
- El administrador nunca escribe datos clínicos.
- Suben documentos el profesional dueño de la atención **o** el administrador.
- Descarga el administrador o el profesional con visibilidad sobre el documento.
- Solo PDF, JPEG y PNG, hasta 10 MB, validados por contenido.
- Solo quien subió puede eliminar; el archivo físico se borra con el registro.
- Se permiten documentos sin atención, ligados al paciente.
- Para profesionales, los documentos sin atención subidos por el administrador
  no son visibles (interpretación aplicada; ver decisiones pendientes).

### Decisiones tomadas para la Etapa 8

- React Router con el token en `sessionStorage` (sobrevive a recargas, no queda
  en disco al cerrar la pestaña).
- Se implementan todos los módulos en la misma etapa, con navegación por rol.
- El dashboard usa contadores calculados con los endpoints existentes; no se
  agregó un endpoint de resumen.
- Selección de pacientes y profesionales por RUT con búsqueda en vivo y retardo.
- Documentos se suben tanto desde la ficha de la atención como desde la ficha
  del paciente (sin atención).
- CSS propio consistente con la paleta carmesí/crema; sin librería de
  componentes.
- El frontend refleja las reglas del backend: no duplica permisos ni debilita
  validaciones; solo oculta acciones que el servidor rechazaría.

### Decisiones tomadas para la Etapa 9

- Se versiona la suite E2E con Playwright en `e2e/`, con Chrome del sistema y
  credenciales por variables de entorno.
- El respaldo incluye base y volumen de documentos, con manifiesto SHA256 y
  verificación automática de restauración en recursos temporales.
- La restauración sobre datos reales es explícita y destructiva: exige
  `-Confirmar` y detiene el backend durante la operación.
- Se mantiene una base limpia: solo cuentas y un profesional sintéticos, sin
  pacientes, citas, atenciones ni documentos.
- Documentación final: README ampliado más manual breve de uso por rol.
- Despliegue: solo local con Docker Compose; sin guía de servidor productivo.

---

## 7. Lo que NO se ha probado

- La suite E2E no se ejecuta en CI ni en otro navegador que no sea Chrome/Edge
  del sistema; no cubre todos los módulos ni todos los caminos de error.
- La persistencia de documentos se verificó en el volumen real con archivos
  pequeños; no se probaron archivos cercanos al límite de 10 MB, cortes de
  conexión ni cargas concurrentes.
- No hay análisis antivirus ni cuarentena de archivos subidos.
- La restauración real de `restauracion.ps1` **no se ejecutó sobre los datos de
  desarrollo**: solo se validó su sintaxis y la guarda `-Confirmar`. La
  restauración completa se probó en recursos temporales con `-Verificar`.
- No se probó una restauración desde otro equipo ni con respaldos antiguos.
- **Concurrencia real:** las pruebas fuerzan las restricciones de la base
  (solapamiento y atención única) sin lanzar dos peticiones HTTP simultáneas.
- No se ha probado el flujo de recuperación de contraseña (no existe).
- No se ha probado en un entorno distinto de este equipo Windows con Docker
  Desktop ni con HTTPS o proxy inverso.

---

## 8. Archivos del proyecto

### 8.1. Versionados (commits `e45174f` … `a732633`)

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
    schemas/{__init__,auth,common,usuario,profesional,paciente,cita,atencion,
             documento}.py
    api/{__init__,comun,deps}.py
    api/v1/{__init__,router,health,auth,usuarios,profesionales,pacientes,citas,
            atenciones,documentos}.py
    services/{__init__,paginacion,usuarios,profesionales,pacientes,citas,
              atenciones,documentos}.py
    cli/{__init__,crear_admin}.py
  migrations/
    env.py                      script.py.mako
    versions/0001_esquema_inicial.py
  tests/{__init__,conftest,apoyo,test_esquema,test_rut,test_auth,test_etapa4,
         test_etapa5,test_etapa6,test_etapa7}.py
frontend/
  .dockerignore                 Dockerfile
  index.html                    package.json
  package-lock.json             vite.config.js
  src/{main.jsx,App.jsx,index.css}
```

### 8.2. Incorporados en el commit de cierre (Etapa 8)

```text
Modificados:
  frontend/index.html                   # favicon
  frontend/package.json                 # react-router-dom 7.18.5, vite 6.4.5
  frontend/src/App.jsx                  # rutas y protección por rol
  frontend/src/index.css                # estilos de todo el sistema
  frontend/src/main.jsx                 # BrowserRouter + AuthProvider

Nuevos:
  frontend/package-lock.json
  frontend/public/favicon.svg
  frontend/src/api.js                   # cliente JWT, errores y descargas
  frontend/src/auth.jsx                 # sesión en sessionStorage y guardas
  frontend/src/formato.js               # fechas, estados, tamaños y etiquetas
  frontend/src/components/Comunes.jsx
  frontend/src/components/Layout.jsx
  frontend/src/components/BuscadorRut.jsx
  frontend/src/components/DocumentosAtencion.jsx
  frontend/src/pages/{Login,Dashboard,Usuarios,Profesionales,Pacientes,Citas,
                      Atenciones,Documentos}.jsx
```

### 8.3. Incorporados en el commit de cierre (Etapa 9)

```text
Modificados:
  README.md                             # instalación, roles, pruebas, respaldo
  .gitignore                            # informes E2E y respaldos locales

Nuevos:
  MANUAL_USUARIO.md                     # uso por rol
  e2e/package.json
  e2e/package-lock.json
  e2e/playwright.config.js              # Chrome, baseURL e informes
  e2e/limpieza.js                       # borra datos y archivos del RUT de prueba
  e2e/pruebas/flujo-completo.spec.js    # recorrido E2E de 7 pasos
  scripts/respaldo.ps1                  # respaldo + verificación temporal
  scripts/restauracion.ps1              # restauración con -Confirmar
```

### 8.4. Solo local (no versionado)

```text
.env                        # credenciales locales generadas
respaldos/                  # respaldos creados por scripts/respaldo.ps1
e2e/node_modules/           # dependencias instaladas de la suite E2E
e2e/playwright-report/      # informe HTML de la última ejecución
e2e/test-results/           # trazas y capturas de fallos
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

Todas las citas, atenciones, pacientes y documentos usados en las
verificaciones se eliminaron al terminar. El volumen de documentos quedó vacío.
No hay datos clínicos reales.

### 9.1. Base externa (Neon)

El backend toma `DATABASE_URL` desde `.env` y la normaliza a
`postgresql+psycopg://`. Al estar definida, Docker Compose deja de usar la base
local del servicio `db` para el backend; esa base queda como respaldo.

Verificación del 03-11-2026 contra Neon:

| Comprobación | Resultado |
|---|---|
| `/api/v1/health/db` | `ok`, motor `postgresql` |
| `alembic current` | `0001_esquema_inicial (head)` |
| Login administrador (`11111111-1`) | Correcto |
| Login profesional (`12345678-5`) | Correcto |
| Filas: usuarios / profesionales | 2 / 1 |
| Filas clínicas (pacientes, citas, atenciones, documentos) | 0 |

El plan Neon Free es permanente dentro de sus límites (1 GB por proyecto,
100 CU-horas al mes y suspensión por inactividad). No expira a los 30 días como
la base gratuita de Render y no borra datos al alcanzar el límite.

---

## 10. Comandos de operación

```bash
docker compose up -d --build

docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
docker compose exec backend alembic check

docker compose exec backend pytest
docker compose exec backend pytest tests/test_etapa7.py -v

docker compose exec frontend npm install
docker compose exec frontend npm audit
docker compose exec frontend npm run build

docker compose exec backend python -m app.cli.crear_admin \
  --rut 11111111-1 --nombres Ana --apellidos Administradora \
  --correo ana@ejemplo.cl
```

Pruebas de extremo a extremo y respaldo (PowerShell):

```powershell
cd e2e
npm install
$env:DISS_E2E_ADMIN_PASSWORD = "clave-del-administrador"
$env:DISS_E2E_PROF_PASSWORD  = "clave-del-profesional"
npx playwright test
cd ..

.\scripts\respaldo.ps1 -Verificar

.\scripts\restauracion.ps1 `
  -Base .\respaldos\base_YYYYMMDD_HHMMSS.dump `
  -Documentos .\respaldos\documentos_YYYYMMDD_HHMMSS.tar.gz `
  -Confirmar
```

- Frontend: <http://localhost:5173>
- Swagger: <http://localhost:8000/docs>
- Salud: <http://localhost:8000/api/v1/health>

Las pruebas crean y eliminan `citas_municipales_test`; nunca tocan la base de
desarrollo. Si una ejecución se interrumpe, puede quedar un `pytest` huérfano
que elimine esa base a mitad de la siguiente ejecución. Las pruebas de
documentos usan un directorio temporal y no escriben en el volumen real.

Para incorporar `python-multipart` fue necesario reconstruir la imagen del
backend (`docker compose build backend` + `docker compose up -d backend`).

---

## 11. Cierre de las Etapas 5 a 9

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
| Commit de la etapa | Cumplido (`0fd83d4`) |

### Etapa 7 — Documentos privados

| Criterio | Estado |
|---|---|
| Profesional dueño o administrador suben | Cumplido |
| Validación por contenido, no por cabecera | Cumplido (415) |
| Límite de 10 MB | Cumplido (413) |
| Nombre original saneado y clave generada por el servidor | Cumplido |
| Documento sin atención ligado al paciente | Cumplido |
| Coherencia paciente/atención | Cumplido (422) |
| Visibilidad por rol y propiedad | Cumplido (404) |
| Descarga protegida y con bytes idénticos | Cumplido |
| Borrado solo por el autor | Cumplido (403/404) |
| Archivo físico eliminado con el registro | Cumplido (volumen vacío) |
| Pruebas propias | 14 passed |
| Commit de la etapa | Cumplido (`a732633`) |

`alembic check` responde «No new upgrade operations detected»: las Etapas 5 a 8
no introdujeron cambios de esquema.

### Etapa 8 — Frontend completo

| Criterio | Estado |
|---|---|
| Login y sesión con token en `sessionStorage` | Cumplido |
| Rutas protegidas y por rol | Cumplido (`/usuarios` solo administrador) |
| Dashboard con contadores de la API actual | Cumplido |
| Usuarios (solo administrador) | Cumplido |
| Profesionales y pacientes con filtros y paginación | Cumplido |
| Citas: alta, confirmación, cancelación y ausencia | Cumplido |
| Atención desde cita confirmada y corrección del registro | Cumplido |
| Autocompletado por RUT con búsqueda en vivo | Cumplido |
| Subida de documentos desde atención y paciente | Cumplido |
| Descarga autenticada con nombre original | Cumplido |
| Borrado de documentos solo por el autor | Cumplido |
| Mensajes de error uniformes y 401 | Cumplido |
| `npm run build` | Correcto (Vite 6.4.5) |
| `npm audit` | 0 vulnerabilidades |
| Flujo E2E en navegador real | 12 comprobaciones correctas (sección 4.11) |
| Commit de la etapa | Cumplido |

La Etapa 8 no modificó el backend ni el esquema; `alembic check` sigue limpio.

### Etapa 9 — Integración y cierre

| Criterio | Estado |
|---|---|
| Suite E2E versionada con Playwright | Cumplido (`e2e/`) |
| Recorrido completo: login, paciente, cita, atención y documentos | Cumplido |
| Control de acceso por rol verificado desde la interfaz | Cumplido (`/usuarios` bloqueado) |
| Limpieza de datos y archivos del RUT de prueba | Cumplido (0 filas y 0 archivos) |
| Credenciales fuera del repositorio | Cumplido (variables de entorno) |
| Respaldo de base, documentos y manifiesto SHA256 | Cumplido |
| Restauración verificada en recursos temporales | Cumplido (conteos y contenido idénticos) |
| Restauración real protegida por `-Confirmar` | Cumplido (sintaxis y guarda validadas) |
| README ampliado | Cumplido |
| Manual de usuario por rol | Cumplido (`MANUAL_USUARIO.md`) |
| Base final sin datos clínicos | Cumplido (2 usuarios, 1 profesional, 0 registros) |
| Commit de la etapa | Cumplido |

La Etapa 9 no modificó backend, frontend ni esquema; la suite de backend y
`alembic check` se mantienen sin cambios.

---

## 12. Etapa 9 — Alcance ejecutado

**Objetivo:** consolidar el MVP: pruebas de extremo a extremo versionadas,
respaldo y restauración de base de datos y volumen de documentos, documentación
final y criterios de operación.

**Decisiones aplicadas:**

1. **Integración:** se versiona la suite E2E con Playwright; no se ejecuta en CI.
2. **Respaldo:** `pg_dump` + copia del volumen, con verificación automática de la
   restauración en recursos temporales.
3. **Datos finales:** base limpia, solo con cuentas y un profesional sintéticos.
4. **Documentación:** README ampliado y manual breve de usuario por rol.
5. **Despliegue:** solo local con Docker Compose; sin guía de servidor.
6. **Seguridad:** las limitaciones conocidas (auditoría, recuperación de acceso,
   antivirus y retención) quedan documentadas y fuera del alcance del MVP.

**Requisito previo:** cerrado (commit de cierre de la Etapa 8).

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
| 29-10-2026 | Verificación manual por HTTP de la Etapa 6 | 11 comprobaciones correctas (sección 4.9) |
| 29-10-2026 | `docker compose build backend` + `up -d backend` | `python-multipart` 0.0.20 disponible |
| 29-10-2026 | `pytest tests/test_etapa7.py` | 14 passed |
| 29-10-2026 | `pytest` (suite completa) | **133 passed**, 1 warning |
| 29-10-2026 | Verificación manual por HTTP de la Etapa 7 | 11 comprobaciones correctas, volumen vacío (sección 4.10) |
| 02-11-2026 | `npm install` + `npm audit` del frontend | 0 vulnerabilidades |
| 02-11-2026 | `npm run build` (Vite 6.4.5) | Correcto, 54 módulos |
| 02-11-2026 | `pytest` (suite completa, sin cambios de backend) | **133 passed**, 1 warning |
| 02-11-2026 | `pytest` (re-ejecución final tras la Etapa 9) | **133 passed**, 1 warning (539.56s) |
| 02-11-2026 | `alembic check` tras la Etapa 8 | «No new upgrade operations detected» |
| 02-11-2026 | Flujo E2E en Chrome headless (Etapa 8) | 12 comprobaciones correctas, sin errores de consola |
| 02-11-2026 | Limpieza de datos E2E y volumen | 0 filas sintéticas; volumen vacío |
| 02-11-2026 | Suite E2E versionada (`e2e/`) con limpieza reforzada | `1 passed (1.2m)`, 7 pasos |
| 02-11-2026 | Datos y archivos del RUT de prueba tras la suite | 0 filas en 4 tablas; 0 archivos |
| 02-11-2026 | `respaldo.ps1 -Verificar` con volumen vacío | Conteos `2,1,0,0,0,0,1`; 0 documentos |
| 02-11-2026 | `respaldo.ps1 -Verificar` con 1 documento sintético | Conteos idénticos; contenido idéntico |
| 02-11-2026 | Sintaxis de `respaldo.ps1` y `restauracion.ps1` | Correcta (parser de PowerShell) |
| 02-11-2026 | `restauracion.ps1` sin `-Confirmar` | Cancela sin tocar datos; código 1 |
| 03-11-2026 | Publicación en GitHub | `main` subida; `.env` y claves fuera del repositorio |

---

## 14. Notas y advertencias

- El contenedor `diss_backend` ejecuta el código del árbol de trabajo mediante
  `uvicorn --reload`; el contenedor `diss_frontend` usa Vite dev con bind mount.
- La imagen del backend fue reconstruida para incluir `python-multipart`; un
  `docker compose up` sin `--build` puede dejar la dependencia ausente.
- El frontend incorpora `react-router-dom` y Vite 6.4.5; tras cambiar
  `package.json` hay que ejecutar `npm install` y reiniciar el contenedor.
- El repositorio remoto es <https://github.com/Adelxs/aplicacion_Discapacidad>;
  la rama `main` está publicada y no se versionan `.env`, respaldos ni claves.
- El proyecto `aplicacion_SSEE` no ha sido modificado ni consultado.
- No se usan datos clínicos reales; todos los datos de prueba son sintéticos.
- No se deben ejecutar `docker compose down -v` ni `alembic downgrade` sin
  autorización: eliminan datos, archivos y esquema.
- Las correcciones de atenciones no dejan traza hasta que exista auditoría.
- Los documentos no se eliminan al borrar un paciente con historial (el borrado
  está restringido); el respaldo del volumen se cubre con `scripts/respaldo.ps1`,
  pero no hay política de retención ni respaldos programados.
- La suite E2E usa el RUT sintético `77777777-7` y borra sus datos y archivos;
  no debe cambiarse por un RUT real. Sus contraseñas se pasan por variables de
  entorno y no se versionan.
- `respaldos/` contiene datos personales y clínicos: no se versiona y debe
  copiarse a un medio seguro.
- `restauracion.ps1` reemplaza la base y los documentos; sin `-Confirmar` no
  ejecuta ninguna operación destructiva.
