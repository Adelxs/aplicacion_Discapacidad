const ZONA = "America/Santiago";

const FORMATO_FECHA_HORA = new Intl.DateTimeFormat("es-CL", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: ZONA,
});

const FORMATO_HORA = new Intl.DateTimeFormat("es-CL", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: ZONA,
});

export function formatearFechaHora(valor) {
  if (!valor) return "—";
  return FORMATO_FECHA_HORA.format(new Date(valor));
}

export function formatearFecha(valor) {
  if (!valor) return "—";
  const [anio, mes, dia] = String(valor).slice(0, 10).split("-");
  if (!anio || !mes || !dia) return String(valor);
  return `${dia}-${mes}-${anio}`;
}

export function formatearHora(valor) {
  if (!valor) return "—";
  return FORMATO_HORA.format(new Date(valor));
}

export function formatearRango(inicio, fin) {
  if (!inicio || !fin) return "—";
  return `${formatearFechaHora(inicio)} – ${formatearHora(fin)}`;
}

/** Convierte una fecha ISO al valor que espera un input datetime-local. */
export function aDatetimeLocal(valor) {
  if (!valor) return "";
  const fecha = new Date(valor);
  const partes = new Intl.DateTimeFormat("en-CA", {
    timeZone: ZONA,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(fecha);

  const valorDe = (tipo) => partes.find((parte) => parte.type === tipo)?.value;
  return `${valorDe("year")}-${valorDe("month")}-${valorDe("day")}T${valorDe("hour")}:${valorDe("minute")}`;
}

export function formatearTamano(bytes) {
  if (bytes == null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function etiquetaEstado(estado) {
  const etiquetas = {
    pendiente: "Pendiente",
    confirmada: "Confirmada",
    atendida: "Atendida",
    cancelada: "Cancelada",
    ausente: "Ausente",
  };
  return etiquetas[estado] ?? estado;
}

export function etiquetaRol(rol) {
  return rol === "administrador" ? "Administrador" : "Profesional";
}

export function etiquetaTipoMime(tipo) {
  const etiquetas = {
    "application/pdf": "PDF",
    "image/jpeg": "JPEG",
    "image/png": "PNG",
  };
  return etiquetas[tipo] ?? tipo;
}

export function nombreCompleto(persona) {
  if (!persona) return "—";
  return `${persona.nombres ?? ""} ${persona.apellidos ?? ""}`.trim() || "—";
}
