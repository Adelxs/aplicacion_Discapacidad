# Manual de usuario — Sistema Municipal de Citas y Atenciones

Este manual describe el uso del MVP por rol. No reemplaza los procedimientos
internos del centro de salud ni las obligaciones de confidencialidad.

> **Importante:** el sistema es un MVP para ejecución local. No cargue datos
> clínicos reales en este entorno de desarrollo.

## 1. Ingreso y sesión

1. Abra <http://localhost:5173>.
2. Ingrese su **RUT** (con o sin puntos; el sistema lo normaliza) y su
   contraseña.
3. Pulse **Ingresar**.

La sesión se guarda en la pestaña actual: se mantiene al recargar, pero se
pierde al cerrarla. Si el token expira o la cuenta se desactiva, la próxima
operación devuelve al inicio de sesión. Para salir, use **Cerrar sesión** en la
barra lateral.

Si ve el mensaje «No se pudo validar la sesión», vuelva a ingresar. Los errores
de credenciales no indican si el RUT existe.

## 2. Elementos comunes

- **Menú lateral:** cambia según el rol. El profesional no ve **Usuarios**.
- **Resumen:** muestra contadores de citas por estado, atenciones, pacientes,
  profesionales y documentos. El administrador ve además los usuarios.
- **Filtros:** se completan y se aplican con **Buscar**. La paginación se
  controla con **Anterior** y **Siguiente**.
- **Fechas y horas:** se muestran en la zona `America/Santiago`.
- **Avisos:** los mensajes verdes confirman una acción; los rojos explican un
  error. Los modales se cierran con la **X**, el botón **Cancelar** o `Escape`.
- **Autocompletado por RUT:** al escribir al menos dos caracteres aparecen
  coincidencias; haga clic en una para seleccionar el paciente. Si no elige una
  sugerencia, el formulario puede rechazar el RUT.

## 3. Rol administrador

### 3.1. Usuarios

**Usuarios → Nuevo usuario**

- Complete RUT, nombres, apellidos, correo, rol y contraseña inicial (mínimo 8
  caracteres).
- El RUT no se puede modificar después de crear la cuenta.
- **Editar** permite cambiar nombres, correo, rol y estado activo.
- No es posible cambiar el propio rol ni desactivar la propia cuenta desde la
  interfaz.
- Una cuenta desactivada pierde acceso de inmediato.

### 3.2. Profesionales

**Profesionales → Nuevo profesional**

- Complete RUT, nombres, apellidos, especialidad, teléfono y correo.
- **Cuenta vinculada (RUT)** es opcional. Si la indica, debe existir una cuenta
  con rol **profesional** y exactamente el mismo RUT.
- El perfil debe estar activo para que el profesional pueda agendar.
- La vinculación puede definirse al crear el perfil y modificarse en la edición;
  siempre debe apuntar a una cuenta profesional con el mismo RUT.

### 3.3. Pacientes

**Pacientes → Nuevo paciente**

- Complete RUT, nombres, apellidos, fecha de nacimiento, teléfono, correo y
  dirección. La fecha de nacimiento no puede ser futura.
- **Editar** actualiza los datos de contacto y el estado.
- **Eliminar** solo funciona si el paciente no tiene citas, atenciones ni
  documentos. Si tiene historial, el sistema muestra un conflicto y no borra
  nada.
- **Documentos** abre la bandeja de documentos filtrada por ese paciente.

### 3.4. Citas y agenda

- El administrador **consulta toda la agenda**, pero no crea, confirma, cancela
  ni marca ausencias.
- Puede filtrar por RUT del paciente, estado y rango de fechas.
- **Ver** muestra el detalle completo.
- **Observaciones** permite agregar, modificar o borrar una nota
  administrativa (máximo 1.000 caracteres). No modifica el registro clínico.

### 3.5. Atenciones

- Ve todas las atenciones del sistema.
- **Ver ficha** muestra el registro clínico, sus datos de auditoría básicos y los
  documentos adjuntos.
- El administrador no registra ni corrige atenciones.
- Puede subir documentos a cualquier paciente o atención y descargar cualquiera.

### 3.6. Documentos

**Documentos** permite:

- Elegir un paciente por RUT.
- Asociar el archivo a una atención del paciente o dejarlo **sin atención**.
- Subir PDF, JPEG o PNG de hasta 10 MB.
- Filtrar por RUT y descargar los documentos visibles.
- Eliminar únicamente los documentos que usted subió.

## 4. Rol profesional

### 4.1. Agenda

**Citas → Nueva cita**

- Seleccione el paciente por RUT.
- Indique inicio, fin y motivo. El fin debe ser posterior al inicio.
- La cita se crea a su nombre y queda **pendiente**.
- El sistema rechaza horarios que se solapan con otra cita activa. Las citas
  canceladas liberan el horario.

Acciones sobre una cita propia:

| Acción | Cuándo aparece |
|---|---|
| **Confirmar** | Cita pendiente |
| **Registrar atención** | Cita confirmada |
| **Ausente** | Cita confirmada |
| **Cancelar** | Cita pendiente o confirmada |
| **Ver** | Siempre |

Las citas atendidas, canceladas o ausentes son terminales y no se reabren. No
puede operar citas de otro profesional: el sistema responde como si no
existieran.

### 4.2. Registro de la atención

Desde una cita **confirmada**, pulse **Registrar atención**:

- La fecha y hora deben estar dentro del horario de la cita.
- Complete motivo y registro clínico (máximo 10.000 caracteres).
- Al guardar, la cita pasa a **atendida** en la misma operación.
- Una cita admite una sola atención.

### 4.3. Corrección de atenciones

**Atenciones → Ver ficha → Corregir registro**

- Solo el profesional que registró la atención puede corregir motivo y registro
  clínico.
- No se puede cambiar la cita, el paciente ni el profesional.
- No queda una versión anterior ni una traza de auditoría.

### 4.4. Pacientes y profesionales

- **Pacientes**: puede consultar las fichas y abrir sus documentos; no puede
  crear, editar ni eliminar pacientes.
- **Profesionales**: puede consultar perfiles y especialidades; no puede
  crearlos ni editarlos.

### 4.5. Documentos

- Ve los documentos que subió y los de sus propias atenciones.
- Puede subir documentos a sus atenciones o a un paciente sin atención.
- Puede descargar lo que tiene visibilidad.
- Solo puede eliminar los documentos que subió.
- Los documentos sin atención subidos por el administrador no aparecen en su
  bandeja.

## 5. Privacidad y buenas prácticas

- Cierre sesión al alejarse del equipo, especialmente en equipos compartidos.
- No comparta contraseñas ni deje sesiones abiertas en pestañas ajenas.
- Verifique el RUT y el nombre del paciente antes de agendar, atender o subir un
  documento.
- Los documentos son privados: no los descargue a equipos personales ni los
  envíe por canales no institucionales.
- Ante un error 403, no insista: la operación no está permitida para su rol. Ante
  un 404 en un recurso que esperaba ver, confirme que sea suyo.
- Si el sistema rechaza un archivo, compruebe que sea PDF, JPEG o PNG y que no
  supere 10 MB.

## 6. Limitaciones conocidas

- No hay recuperación de contraseña ni registro público.
- No hay auditoría de cambios ni historial de versiones.
- No hay antivirus ni cuarentena de archivos.
- No hay notificaciones, recordatorios ni integración con otros sistemas.
- El sistema está pensado para ejecución local con Docker Compose; no incluye
  HTTPS ni despliegue en servidor.
