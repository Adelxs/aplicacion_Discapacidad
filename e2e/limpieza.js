import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

/** Paciente sintético exclusivo de las pruebas E2E. */
export const RUT_PRUEBA = "77777777-7";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CLAVE_VALIDA = /^[A-Za-z0-9._-]+$/;

function ejecutarDocker(argumentos, opciones = {}) {
  return execFileSync("docker", argumentos, {
    cwd: RAIZ,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    ...opciones,
  });
}

function datosBase() {
  return {
    usuario: process.env.DISS_DB_USER ?? "citas_app",
    base: process.env.DISS_DB_NAME ?? "citas_municipales",
  };
}

function consultarClavesArchivo({ usuario, base }) {
  const salida = ejecutarDocker([
    "compose",
    "exec",
    "-T",
    "db",
    "psql",
    "-t",
    "-A",
    "-v",
    "ON_ERROR_STOP=1",
    "-U",
    usuario,
    "-d",
    base,
    "-c",
    `SELECT clave_archivo FROM documentos WHERE paciente_rut = '${RUT_PRUEBA}'`,
  ]);

  return salida
    .split(/\r?\n/)
    .map((linea) => linea.trim())
    .filter((linea) => linea.length > 0 && CLAVE_VALIDA.test(linea));
}

/**
 * Elimina los datos clínicos y los archivos del RUT de prueba en el orden que
 * exigen las claves foráneas. Solo toca ese RUT; nunca datos reales ni otros
 * pacientes. Requiere el entorno Docker levantado (db, backend y frontend).
 */
export function limpiarDatosPrueba() {
  const datos = datosBase();
  let claves = [];

  try {
    claves = consultarClavesArchivo(datos);
  } catch (fallo) {
    const detalle = fallo.stderr?.trim() || fallo.message;
    throw new Error(
      `No se pudieron consultar los documentos E2E (${RUT_PRUEBA}). ` +
        `Verifique que "docker compose" esté levantado.\n${detalle}`,
    );
  }

  const sql = [
    `DELETE FROM documentos WHERE paciente_rut = '${RUT_PRUEBA}'`,
    `DELETE FROM atenciones WHERE paciente_rut = '${RUT_PRUEBA}'`,
    `DELETE FROM citas WHERE paciente_rut = '${RUT_PRUEBA}'`,
    `DELETE FROM pacientes WHERE rut = '${RUT_PRUEBA}'`,
  ].join("; ");

  try {
    ejecutarDocker([
      "compose",
      "exec",
      "-T",
      "db",
      "psql",
      "-v",
      "ON_ERROR_STOP=1",
      "-U",
      datos.usuario,
      "-d",
      datos.base,
      "-c",
      `${sql};`,
    ]);
  } catch (fallo) {
    const detalle = fallo.stderr?.trim() || fallo.message;
    throw new Error(
      `No se pudieron limpiar los datos E2E (${RUT_PRUEBA}). ` +
        `Verifique que las variables DISS_DB_USER/DISS_DB_NAME sean correctas.\n${detalle}`,
    );
  }

  if (claves.length > 0) {
    try {
      ejecutarDocker([
        "compose",
        "exec",
        "-T",
        "backend",
        "rm",
        "-f",
        ...claves.map((clave) => `/data/documentos/${clave}`),
      ]);
    } catch (fallo) {
      const detalle = fallo.stderr?.trim() || fallo.message;
      throw new Error(
        `No se pudieron eliminar los archivos E2E del volumen de documentos.\n${detalle}`,
      );
    }
  }
}
