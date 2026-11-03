
const API_URL = import.meta.env.VITE_API_URL ?? "https://aplicacion-discapacidad-1.onrender.com/";

let tokenActual = null;

/** Fija el token que se enviara en las siguientes peticiones. */
export function configurarToken(token) {
  tokenActual = token ?? null;
}

export class ErrorAPI extends Error {
  constructor(mensaje, estado, codigo, detalle) {
    super(mensaje);
    this.name = "ErrorAPI";
    this.estado = estado;
    this.codigo = codigo;
    this.detalle = detalle;
  }
}

async function leerCuerpo(respuesta) {
  const texto = await respuesta.text();
  if (!texto) return null;
  try {
    return JSON.parse(texto);
  } catch {
    return null;
  }
}

function errorDesde(respuesta, cuerpo) {
  const error = cuerpo?.error ?? {};
  const detalle = Array.isArray(error.detalle) ? error.detalle : null;
  let mensaje = error.mensaje ?? `Error HTTP ${respuesta.status}`;

  if (detalle?.length) {
    const campos = detalle
      .map((item) => (item.campo ? `${item.campo}: ${item.mensaje}` : item.mensaje))
      .join(" · ");
    mensaje = `${mensaje} ${campos}`;
  }

  return new ErrorAPI(
    mensaje,
    respuesta.status,
    error.codigo ?? "error",
    error.detalle ?? null,
  );
}

function cabeceras(extra = {}) {
  const resultado = { Accept: "application/json", ...extra };
  if (tokenActual) resultado.Authorization = `Bearer ${tokenActual}`;
  return resultado;
}

/**
 * Ejecuta una peticion a la API.
 * - `cuerpo` objeto se envia como JSON; un FormData se envia tal cual.
 * - Un 401 avisa al proveedor de sesion para cerrar la sesion.
 */
export async function pedir(ruta, { metodo = "GET", cuerpo } = {}) {
  const opciones = { method: metodo, headers: cabeceras() };

  if (cuerpo instanceof FormData) {
    opciones.body = cuerpo;
  } else if (cuerpo !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(cuerpo);
  }

  const respuesta = await fetch(`${API_URL}${ruta}`, opciones);

  if (respuesta.status === 401) {
    window.dispatchEvent(new CustomEvent("diss:sesion-expirada"));
  }

  const datos = respuesta.status === 204 ? null : await leerCuerpo(respuesta);

  if (!respuesta.ok) {
    throw errorDesde(respuesta, datos);
  }
  return datos;
}

/** Descarga un archivo protegido y lo entrega al navegador. */
export async function descargar(ruta, nombreSugerido = "documento") {
  const respuesta = await fetch(`${API_URL}${ruta}`, {
    headers: cabeceras(),
  });

  if (respuesta.status === 401) {
    window.dispatchEvent(new CustomEvent("diss:sesion-expirada"));
  }

  if (!respuesta.ok) {
    const datos = await leerCuerpo(respuesta);
    throw errorDesde(respuesta, datos);
  }

  const blob = await respuesta.blob();
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombreSugerido || "documento";
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}
