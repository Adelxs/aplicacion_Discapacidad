# Estado del proyecto — `aplicacion_DISS`

**Fecha de corte:** 28 de octubre de 2026
**Documento de referencia:** Documento Maestro de Especificaciones v1.0
**Alcance:** Sistema Municipal de Gestión de Citas y Atenciones — MVP

> Este documento refleja únicamente lo verificado hasta la fecha de corte.
> Las Etapas 1 a 4 están completas y con la suite en verde. La Etapa 4 **aún no
> tiene commit**: los cambios están en el árbol de trabajo.

---

## 1. Resumen ejecutivo

| Aspecto | Estado real |
|---|---|
| Entorno Docker (PostgreSQL + FastAPI + React) | Funcionando, 3 servicios arriba |
| Migración inicial aplicada | Sí (`0001_esquema_inicial`, head) |
| Etapas 1, 2 y 3 | Completadas, probadas y verificadas |
| Etapa 4 (usuarios, profesionales, pacientes) | **Completada y verificada** (sin commit) |
| Etapas 5 a 9 | No iniciadas |
| Repositorio remoto (GitHub) | **No existe**; solo repositorio local |
| Último commit | `81031b3` (cierre de Etapa 3) |
| Cambios de Etapa 4 en git | **Sin commit** (4 modificados + 16 nuevos = 20 archivos de la etapa, más este documento) |

**Resultado de la última ejecución completa de pruebas (28-10-2026):**

```text
77 passed, 1 warning in 80.77s
```

La última ejecución se hizo sobre el árbol actual con
`TEST_DATABASE_NAME=citas_municipales_test_etapa4_final` para aislarla de
procesos concurrentes.

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
| Pruebas | pytest 8.3.4 + httpx 0.28.1 |
| Contenedores | Docker 29.8.2 + Compose v5.5.1 |

**Puertos:** frontend `5173`, API `8000`, PostgreSQL `5433` en el host
(el `5432` local está ocupado por otro PostgreSQL).

**Servicios al corte:** `diss_db` (healthy), `diss_backend` (healthy,
con `uvicorn --reload` sobre `/app/app`), `diss_frontend` (up).

---

## 3. Estado por etapas

| Etapa | Estado | Evidencia de verificación |
|---|---|---|
| 1. Estructura, configuración y salud | **Completada** | 3 contenedores arriba; `/api/v1/health` y `/health/db` responden 200; CORS correcto |
| 2. Modelos ORM y migraciones | **Completada** | Migración aplicada en base de desarrollo y en base nueva de pruebas; `alembic check` sin diferencias; 19 pruebas de esquema en verde |
| 3. Autenticación y autorización | **Completada** | Login y `/auth/me` verificados contra la API real; 401 en casos inválidos; 403 por rol |
| 4. Usuarios, profesionales y pacientes | **Completada** | 26 pruebas de la etapa en verde y suite completa en 77 passed; verificación manual por HTTP (ver 5.4) |
| 5. Citas y agenda | No iniciada | — |
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
- Manejo uniforme de errores con formato `{"error": {"codigo", "mensaje", "detalle"}}`.
- CORS restringido a `http://localhost:5173`.
- Frontend mínimo que consulta `/health` y `/health/db` y muestra el resultado.

### 4.2. Base de datos (Etapa 2)

Seis tablas: `usuarios`, `profesionales`, `pacientes`, `citas`, `atenciones`,
`documentos`, más `alembic_version`.

Restricciones verificadas con pruebas:

- RUT canónico (`12345678-9`) por `CHECK`.
- `fecha_hora_fin > fecha_hora_inicio`.
- Estados de cita limitados a cinco valores.
- Una atención por cita (`UNIQUE`).
- Coherencia paciente/profesional mediante **FK compuesta** contra la cita.
- Documento asociado a una atención debe pertenecer al mismo paciente.
- **Sin solapamientos de agenda** con `EXCLUDE USING gist`, ignorando citas
  canceladas (protección a nivel de base de datos, válida ante concurrencia).
- Pacientes con historial no eliminables (`ON DELETE RESTRICT`).
- Cuenta vinculada a profesional debe tener el mismo RUT (`CHECK`).

### 4.3. Autenticación y autorización (Etapa 3)

- `POST /api/v1/auth/login` y `GET /api/v1/auth/me`.
- Contraseñas con **Argon2id**.
- JWT HS256 firmado con `SECRET_KEY`; expiración de 480 minutos configurable.
- Token solo con `sub`, `rol`, `iat`, `exp` (sin contraseña ni datos clínicos).
- Mensaje de error genérico para RUT inexistente, contraseña incorrecta,
  RUT inválido y cuenta desactivada.
- Cuenta desactivada pierde acceso de inmediato aunque el token siga vigente.
- Dependencias `requiere_roles`, `requiere_administrador`, `requiere_profesional`
  con respuesta 403 verificada por HTTP.
- Normalización y validación de RUT por módulo 11, con pruebas unitarias.
- CLI `python -m app.cli.crear_admin` para crear la cuenta inicial.

### 4.4. Usuarios, profesionales y pacientes (Etapa 4)

| Recurso | Endpoints | Permisos |
|---|---|---|
| Usuarios | `GET`, `POST`, `GET/{rut}`, `PATCH/{rut}` | Solo administrador |
| Profesionales | `GET`, `POST`, `GET/{rut}`, `PATCH/{rut}` | Consulta: ambos roles. Alta/edición: solo administrador |
| Pacientes | `GET`, `POST`, `GET/{rut}`, `PATCH/{rut}`, `DELETE/{rut}` | Consulta: ambos roles. Alta/edición/borrado: solo administrador |

Comportamiento verificado:

- Normalización de RUT en altas y en rutas (`12.345.678-5` → `12345678-5`);
  RUT inválido en ruta responde 404 y en cuerpo 422.
- Validación de correo con `EmailStr`; la contraseña nunca se devuelve
  (`password_hash` no aparece en ninguna respuesta).
- Paginación en servidor (`page`, `per_page`, `total`, `pages`) con
  `per_page` limitado a 100.
- Búsqueda parcial por RUT (acepta RUT con puntos) y filtros por `rol`,
  `activo` y `especialidad`.
- Duplicados responden 409 con `codigo = "conflicto"`.
- Vinculación de profesional a cuenta: exige mismo RUT (422 si difiere),
  cuenta existente (404) y rol profesional (409).
- Borrado de paciente: 204 sin historial; 409 con citas, atenciones o
  documentos asociados; 404 si no existe; 403 para profesionales.

---

## 5. Etapa 4: diagnóstico de los fallos y resolución

### 5.1. Punto de partida

La etapa se había implementado pero la suite terminaba en
`13 failed, 64 passed`. El análisis de los 13 fallos dio dos causas distintas.

### 5.2. Causa 1 (12 fallos): datos de prueba, no código

`Pydantic EmailStr` (con `email-validator` 2.2.0) rechaza dominios reservados
como `.test`. Los payloads de prueba usaban `nora@ejemplo.test`,
`rita@ejemplo.test`, `sofia@ejemplo.test`, etc., por lo que las altas
respondían **422 antes de llegar a la lógica de negocio**.

Comprobación empírica dentro del contenedor:

```text
FAIL nora@ejemplo.test  -> The part after the @-sign is a special-use
                           or reserved name that cannot be used with email.
OK   nora@ejemplo.cl
OK   nora@example.com
OK   nora@example.org
```

**Conclusión:** el defecto estaba en los datos de prueba. **No se relajó ni
desactivó la validación**; se mantiene `EmailStr` tal como exige la
especificación. Los correos de los payloads de `tests/test_etapa4.py` se
cambiaron a dominio `@ejemplo.cl` (los fixtures que insertan por SQL directo
conservan `.test`, porque no pasan por `EmailStr`).

### 5.3. Causa 2 (1 fallo): expectativa desalineada con el mensaje

`test_no_eliminar_paciente_con_historial` esperaba la palabra «historial» en
el mensaje de error, mientras el servicio respondía «El paciente tiene citas,
atenciones o documentos asociados y no puede eliminarse». El comportamiento
(409) era correcto.

**Resolución:** el mensaje del servicio se redactó como «El paciente tiene
historial asociado (citas, atenciones o documentos) y no puede eliminarse»,
que describe el mismo hecho y usa el término del dominio. La prueba ahora
comprueba además el código de error:

```python
assert respuesta.status_code == 409
error = respuesta.json()["error"]
assert error["codigo"] == "conflicto"
assert "historial" in error["mensaje"].lower()
```

### 5.4. Verificación manual contra la API real (28-10-2026)

Ejecutada con `httpx` contra `http://localhost:8000` (uvicorn real, no
`TestClient`), con datos sintéticos:

| Comprobación | Resultado |
|---|---|
| `POST /auth/login` administrador | 200 |
| `POST /usuarios` (alta de profesional) | 201, sin `password_hash` en la respuesta |
| Login del usuario recién creado (`12345678-5`) | 200 |
| `GET /usuarios` con token de profesional | 403 `sin_permisos` |
| `POST /usuarios` con token de profesional | 403 `sin_permisos` |
| `POST /profesionales` con cuenta vinculada | 201, `usuario_rut` correcto |
| `GET /profesionales/{rut}` con token de profesional | 200 |
| `POST /pacientes` | 201 |
| `GET /pacientes/{rut}` con token de profesional | 200, sin `password_hash` |
| `DELETE /pacientes/{rut}` sin historial | 204, cuerpo vacío |
| `GET /pacientes/{rut}` tras el borrado | 404 `no_encontrado` |
| `DELETE /pacientes/{rut}` con una cita asociada | 409 `conflicto` |
| `DELETE` tras retirar la cita de prueba | 204 |

La cita usada para provocar el 409 se insertó y eliminó por SQL durante la
verificación; no quedó ningún paciente ni cita de prueba.

La verificación se repitió además con una instancia temporal de `uvicorn` en
el puerto `8011` y una base aislada (`citas_municipales_verif_etapa4`), con
resultados idénticos: login `200`, alta y login de usuario `201/200`, `403`
del profesional en `/usuarios`, altas de profesional y paciente `201`,
borrado sin historial `204` y con historial `409`. La base temporal se eliminó
al finalizar.

### 5.5. Incidencia de entorno durante las pruebas

Se detectaron procesos `pytest` **huérfanos** (heredados de ejecuciones
anteriores interrumpidas) y una ejecución ajena concurrente dentro del
contenedor. Al terminar su sesión ejecutaban
`DROP DATABASE citas_municipales_test WITH (FORCE)` y abortaban la suite en
curso (`terminating connection due to administrator command`, luego
`database "citas_municipales_test" does not exist`). Se terminaron los procesos
huérfanos y las verificaciones finales se hicieron con una base aislada
mediante `TEST_DATABASE_NAME`, sin modificar la base de desarrollo. Antes de
ejecutar la suite conviene comprobar que no queden procesos `pytest` vivos en
el contenedor.

---

## 6. Pendiente de implementación

- **Etapa 5:** citas y agenda (creación, cancelación, ausencia, permisos por
  propietario, transiciones de estado, concurrencia).
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
- **Campos opcionales de pacientes:** hoy `telefono`, `correo_electronico` y
  `direccion` son obligatorios (lectura literal del documento). Sin confirmar.
- **`tamano_bytes` en documentos:** columna añadida para validar tamaños, no
  listada en el documento. Sin confirmar.
- **Tabla de auditoría:** no creada todavía; necesaria para «actividad
  reciente» del dashboard del administrador.

---

## 7. Lo que NO se ha probado

- No hay pruebas de extremo a extremo desde el navegador.
- El frontend solo muestra el estado de la API; no existen pantallas de
  negocio ni consumo de los endpoints de la Etapa 4 desde la interfaz.
- No se ha probado la persistencia de documentos tras reiniciar contenedores
  (el volumen existe, pero no hay módulo de documentos).
- No se ha probado respaldo ni restauración de la base de datos.
- No se ha probado el comportamiento concurrente a nivel de API (solo la
  restricción `EXCLUDE` a nivel de base de datos).
- No se ha probado el flujo de recuperación de contraseña (no existe).
- No se ha probado el proyecto en un entorno que no sea este equipo Windows
  con Docker Desktop.

---

## 8. Archivos del proyecto

### 8.1. Versionados (commits `e45174f`, `9b34f82`, `81031b3`)

```text
.env.example
.gitattributes
.gitignore
README.md
docker-compose.yml
backend/
  .dockerignore
  Dockerfile
  requirements.txt
  requirements-dev.txt
  alembic.ini
  pytest.ini
  app/
    __init__.py
    main.py
    core/{__init__,config,errors,rut,security}.py
    db/{__init__,base,session}.py
    models/{__init__,enums,usuario,profesional,paciente,cita,atencion,documento}.py
    schemas/{__init__,auth}.py
    api/{__init__,deps}.py
    api/v1/{__init__,router,health,auth}.py
    cli/{__init__,crear_admin}.py
  migrations/
    env.py
    script.py.mako
    versions/0001_esquema_inicial.py
  tests/{conftest,test_esquema,test_rut,test_auth}.py
frontend/
  .dockerignore
  Dockerfile
  index.html
  package.json
  vite.config.js
  src/{main.jsx,App.jsx,index.css}
```

### 8.2. Sin commit (Etapa 4): 20 archivos + este documento

```text
Modificados:
  backend/app/api/v1/router.py          # registra los routers nuevos
  backend/requirements.txt              # agrega email-validator==2.2.0
  backend/tests/conftest.py             # fixtures cliente/usuarios_auth
  backend/tests/test_auth.py            # usa los fixtures compartidos

Nuevos:
  backend/app/api/comun.py              # normalizacion de RUT en rutas
  backend/app/api/v1/usuarios.py
  backend/app/api/v1/profesionales.py
  backend/app/api/v1/pacientes.py
  backend/app/schemas/common.py         # Pagina[T]
  backend/app/schemas/usuario.py
  backend/app/schemas/profesional.py
  backend/app/schemas/paciente.py
  backend/app/services/{__init__,paginacion,usuarios,profesionales,pacientes}.py
  backend/tests/__init__.py
  backend/tests/apoyo.py                # helpers de login/token/override
  backend/tests/test_etapa4.py
  ESTADO_PROYECTO.md
```

Total de la etapa: 4 archivos modificados y 16 nuevos (los cinco de
`services/` se listan en una sola línea). `ESTADO_PROYECTO.md` se suma aparte.

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
  comunicó en la sesión de trabajo y **no se guarda en este documento ni en el
  repositorio**.
- `12345678-5`: usuario profesional sintético creado durante la verificación
  manual, con su perfil de profesional vinculado (`12345678-5`, Psicología).
  Su contraseña es la de los datos de prueba y debe eliminarse o cambiarse
  antes de usar datos reales.

Ambas cuentas son de prueba; no hay datos clínicos reales.

---

## 10. Comandos de operación

```bash
# Levantar el entorno
docker compose up -d --build

# Aplicar migraciones
docker compose exec backend alembic upgrade head

# Estado de la base
docker compose exec backend alembic current
docker compose exec backend alembic check

# Pruebas completas
docker compose exec backend pytest

# Pruebas de una etapa
docker compose exec backend pytest tests/test_etapa4.py -v

# Si hay otra ejecución concurrente, aislar la base de pruebas:
docker compose exec -e TEST_DATABASE_NAME=citas_municipales_test_aislada backend pytest

# Crear cuenta administradora (interactivo)
docker compose exec backend python -m app.cli.crear_admin \
  --rut 11111111-1 --nombres Ana --apellidos Administradora \
  --correo ana@ejemplo.cl
```

- Frontend: <http://localhost:5173>
- Swagger: <http://localhost:8000/docs>
- Salud: <http://localhost:8000/api/v1/health>

Las pruebas de integración crean y eliminan `citas_municipales_test`; nunca
tocan la base de desarrollo. Si una ejecución se interrumpe, puede quedar un
proceso `pytest` huérfano que elimine esa base de pruebas a mitad de la
siguiente ejecución.

---

## 11. Cierre de la Etapa 4

| Criterio | Estado |
|---|---|
| 1. Correos de prueba con dominio aceptado por `email-validator` | Cumplido (`@ejemplo.cl`) |
| 2. Expectativa del mensaje de borrado alineada con el servicio | Cumplido (incluye «historial» y valida `codigo`) |
| 3. Suite completa en verde | Cumplido: `77 passed` |
| 4. Verificación manual por HTTP (altas, login, 403, borrado 204/409) | Cumplido (ver 5.4) |
| 5. Ninguna respuesta incluye `password_hash` | Cumplido (verificado en pruebas y por HTTP) |
| 6. Commit de la etapa | **Pendiente de autorización** |

`alembic check` responde «No new upgrade operations detected»: la Etapa 4 no
introdujo cambios de esquema.

---

## 12. Siguiente etapa propuesta: Etapa 5 — Citas y agenda

**Objetivo:** implementar la reserva y gestión de citas con permisos por
propietario y prevención de solapamientos.

**Criterios de aceptación:**

1. Un profesional puede crear citas solo para sí mismo; el `profesional_rut`
   se determina desde la identidad autenticada, nunca desde el frontend.
2. El administrador puede consultar todas las citas, pero **no** crear,
   modificar, reprogramar ni cancelar.
3. Se rechazan horarios con `fecha_hora_fin <= fecha_hora_inicio` (409/422).
4. Se rechaza el solapamiento con otra cita activa del mismo profesional
   (409), incluyendo solicitudes concurrentes.
5. Una cita cancelada no bloquea el horario.
6. Transiciones permitidas: `pendiente → confirmada | cancelada`;
   `confirmada → atendida | cancelada | ausente`.
   Estados terminales no se modifican.
7. Endpoints de cancelación y ausencia actualizan estado y fecha.
8. Un profesional no puede ver ni modificar citas de otro profesional
   (verificado en backend, no solo en la interfaz).
9. Listados con búsqueda por RUT de paciente, filtros por estado y rango de
   fechas, y paginación en servidor.
10. Pruebas automatizadas de permisos, solapamientos, transiciones y
    concurrencia, todas en verde.
11. Fechas presentadas en `America/Santiago`, almacenadas con zona horaria.

**Requisito previo:** cerrado. La Etapa 4 está en verde; solo falta el commit.

---

## 13. Registro de verificaciones ejecutadas

| Fecha | Verificación | Resultado |
|---|---|---|
| 27-10-2026 | `docker compose up` y healthchecks | 3 servicios healthy |
| 27-10-2026 | `GET /api/v1/health` y `/health/db` | 200 |
| 27-10-2026 | `alembic upgrade head` (base de desarrollo) | OK |
| 27-10-2026 | Migración desde cero en `citas_municipales_test` | OK |
| 27-10-2026 | `alembic check` | «No new upgrade operations detected» |
| 27-10-2026 | `pytest` al cierre de Etapa 2 | 19 passed |
| 27-10-2026 | `pytest` al cierre de Etapa 3 | 51 passed |
| 27-10-2026 | Login y `/auth/me` contra API real | 200 / 200 |
| 27-10-2026 | Casos inválidos de autenticación | 401 |
| 28-10-2026 | `pytest` con Etapa 4 (diagnóstico inicial) | 13 failed, 64 passed |
| 28-10-2026 | Dominios aceptados por `email-validator` 2.2.0 | `.test` rechazado; `.cl`/`.com`/`.org` aceptados |
| 28-10-2026 | `pytest tests/test_etapa4.py` tras corregir datos | 26 passed |
| 28-10-2026 | `pytest` (suite completa, estado final) | **77 passed**, 1 warning |
| 28-10-2026 | `pytest` sobre el árbol actual con base aislada | **77 passed**, 80.77s |
| 28-10-2026 | `alembic check` tras la Etapa 4 | «No new upgrade operations detected» |
| 28-10-2026 | Verificación manual por HTTP de la Etapa 4 | 13 comprobaciones correctas (ver 5.4) |
| 28-10-2026 | Verificación manual adicional en puerto 8011, base aislada | OK, resultados idénticos |

---

## 14. Notas y advertencias

- El contenedor `diss_backend` ejecuta el código del árbol de trabajo mediante
  `uvicorn --reload`, aunque git HEAD no tenga la Etapa 4.
- La Etapa 4 sigue **sin commit**: los 20 archivos de la etapa y este documento
  están en el árbol de trabajo, no en el historial de Git.
- No se ha configurado repositorio remoto ni se ha publicado nada en GitHub.
- El proyecto `aplicacion_SSEE` no ha sido modificado ni consultado.
- No se usan datos clínicos reales; todos los datos de prueba son sintéticos.
- No se deben ejecutar `docker compose down -v` ni `alembic downgrade` sin
  autorización: eliminan datos y esquema.
