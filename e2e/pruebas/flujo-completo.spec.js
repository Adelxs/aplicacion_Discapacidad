import { expect, test } from "@playwright/test";
import fs from "node:fs/promises";

import { RUT_PRUEBA, limpiarDatosPrueba } from "../limpieza.js";

const ADMIN = {
  rut: process.env.DISS_E2E_ADMIN_RUT ?? "11111111-1",
  password: process.env.DISS_E2E_ADMIN_PASSWORD ?? "",
};

const PROFESIONAL = {
  rut: process.env.DISS_E2E_PROF_RUT ?? "12345678-5",
  password: process.env.DISS_E2E_PROF_PASSWORD ?? "",
};

const PDF = Buffer.from("%PDF-1.4\nDocumento sintetico E2E\n%%EOF\n");

function dosDigitos(valor) {
  return String(valor).padStart(2, "0");
}

/** Fecha local en el formato que espera el formulario (YYYY-MM-DDTHH:mm). */
function formatearFechaHora(fecha) {
  return (
    `${fecha.getFullYear()}-${dosDigitos(fecha.getMonth() + 1)}-` +
    `${dosDigitos(fecha.getDate())}T${dosDigitos(fecha.getHours())}:` +
    `${dosDigitos(fecha.getMinutes())}`
  );
}

// Cita futura calculada en tiempo de ejecución para que la suite no caduque.
const inicioCita = new Date();
inicioCita.setDate(inicioCita.getDate() + 45);
inicioCita.setHours(10, 0, 0, 0);
const finCita = new Date(inicioCita.getTime() + 30 * 60 * 1000);
const INICIO_CITA = formatearFechaHora(inicioCita);
const FIN_CITA = formatearFechaHora(finCita);

test.describe.configure({ mode: "serial" });

test.beforeAll(() => {
  if (!ADMIN.password || !PROFESIONAL.password) {
    throw new Error(
      "Defina DISS_E2E_ADMIN_PASSWORD y DISS_E2E_PROF_PASSWORD antes de ejecutar las pruebas.",
    );
  }
  limpiarDatosPrueba();
});

test.afterAll(() => {
  limpiarDatosPrueba();
});

async function iniciarSesion(page, { rut, password }) {
  await page.locator("#rut").fill(rut);
  await page.locator("#password").fill(password);
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: /Hola,/ })).toBeVisible();
}

async function cerrarSesion(page) {
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page).toHaveURL(/\/login$/);
}

test("flujo completo de gestión clínica", async ({ page }) => {
  const errores = [];

  page.on("pageerror", (error) => errores.push(`pageerror: ${error.message}`));
  page.on("dialog", async (dialogo) => {
    await dialogo.accept();
  });
  page.on("response", (respuesta) => {
    if (respuesta.status() >= 500) {
      errores.push(`HTTP ${respuesta.status()}: ${respuesta.url()}`);
    }
  });
  page.on("requestfailed", (peticion) => {
    errores.push(`requestfailed: ${peticion.url()} (${peticion.failure()?.errorText})`);
  });
  page.on("console", (mensaje) => {
    if (mensaje.type() !== "error") return;
    const texto = mensaje.text();
    if (texto.includes("favicon") || texto.includes("Failed to load resource")) return;
    errores.push(`console: ${texto}`);
  });

  await test.step("acceso sin sesión y login del administrador", async () => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login$/);
    await iniciarSesion(page, ADMIN);
    await expect(page.locator(".tarjeta-resumen").first()).toBeVisible();
  });

  await test.step("alta de paciente desde la interfaz", async () => {
    await page
      .locator(".barra-lateral__nav")
      .getByRole("link", { name: "Pacientes", exact: true })
      .click();
    await expect(page.getByRole("heading", { name: "Fichas de pacientes" })).toBeVisible();

    await page.getByRole("button", { name: "Nuevo paciente" }).click();
    const dialogo = page.getByRole("dialog");
    await dialogo.locator("#paciente-rut").fill(RUT_PRUEBA);
    await dialogo.locator("#paciente-nombres").fill("Prueba");
    await dialogo.locator("#paciente-apellidos").fill("Navegador");
    await dialogo.locator("#paciente-nacimiento").fill("1990-01-01");
    await dialogo.locator("#paciente-telefono").fill("+56911112222");
    await dialogo.locator("#paciente-correo").fill("prueba.navegador@ejemplo.cl");
    await dialogo.locator("#paciente-direccion").fill("Calle Sintetica 742");
    await dialogo.getByRole("button", { name: "Guardar" }).click();

    await expect(page.getByText(`Paciente ${RUT_PRUEBA} creado.`)).toBeVisible();
    await expect(
      page.getByRole("row", { name: /Prueba Navegador/ }),
    ).toBeVisible();
  });

  await test.step("el profesional no accede al módulo de usuarios", async () => {
    await cerrarSesion(page);
    await iniciarSesion(page, PROFESIONAL);

    await page.goto("/usuarios");
    await expect(page).toHaveURL(/\/$/);
    await expect(
      page
        .locator(".barra-lateral__nav")
        .getByRole("link", { name: "Usuarios", exact: true }),
    ).toHaveCount(0);
  });

  await test.step("agenda, confirmación y registro de la atención", async () => {
    await page
      .locator(".barra-lateral__nav")
      .getByRole("link", { name: "Citas", exact: true })
      .click();
    await expect(page.getByRole("heading", { name: "Agenda de citas" })).toBeVisible();

    await page.getByRole("button", { name: "Nueva cita" }).click();
    let dialogo = page.getByRole("dialog");
    await dialogo.locator("#cita-paciente").fill(RUT_PRUEBA);
    await dialogo
      .locator(".buscador__opcion")
      .filter({ hasText: "Prueba Navegador" })
      .click();
    await dialogo.locator("#cita-inicio").fill(INICIO_CITA);
    await dialogo.locator("#cita-fin").fill(FIN_CITA);
    await dialogo.locator("#cita-motivo").fill("Verificacion frontend");
    await dialogo.getByRole("button", { name: "Agendar cita" }).click();
    await expect(
      page.getByText("Cita agendada. Queda pendiente de confirmación."),
    ).toBeVisible();

    const fila = page.getByRole("row", { name: /Verificacion frontend/ });
    await expect(fila).toBeVisible();
    await fila.getByRole("button", { name: "Confirmar" }).click();
    await expect(page.getByText("Cita confirmada.")).toBeVisible();

    await fila.getByRole("button", { name: "Registrar atención" }).click();
    dialogo = page.getByRole("dialog");
    await dialogo.locator("#atencion-motivo").fill("Atencion frontend");
    await dialogo
      .locator("#atencion-registro")
      .fill("Registro sintetico desde el navegador. Sin datos reales.");
    await dialogo.getByRole("button", { name: "Registrar atención" }).click();
    await expect(
      page.getByText("Atención registrada. La cita pasó a estado atendida."),
    ).toBeVisible();
    await expect(fila.getByText("Atendida")).toBeVisible();
  });

  await test.step("la sesión persiste al recargar", async () => {
    await page.reload();
    await expect(page.getByRole("heading", { name: "Agenda de citas" })).toBeVisible();
  });

  await test.step("documento de la atención: subida, descarga y borrado", async () => {
    await page
      .locator(".barra-lateral__nav")
      .getByRole("link", { name: "Atenciones", exact: true })
      .click();
    await expect(page.getByRole("heading", { name: "Registros de atención" })).toBeVisible();

    await page
      .getByRole("row", { name: /Atencion frontend/ })
      .getByRole("button", { name: "Ver ficha" })
      .click();

    const dialogo = page.getByRole("dialog");
    await expect(
      dialogo.getByText("Registro sintetico desde el navegador. Sin datos reales."),
    ).toBeVisible();

    await dialogo.locator('input[type="file"]').setInputFiles({
      name: "prueba.pdf",
      mimeType: "application/pdf",
      buffer: PDF,
    });
    await dialogo.getByRole("button", { name: "Adjuntar" }).click();
    await expect(dialogo.getByText("Documento adjuntado.")).toBeVisible();
    await expect(dialogo.getByText("prueba.pdf")).toBeVisible();

    const [descarga] = await Promise.all([
      page.waitForEvent("download"),
      dialogo.getByRole("button", { name: "Descargar" }).click(),
    ]);
    const ruta = await descarga.path();
    expect(ruta).not.toBeNull();
    const bytes = await fs.readFile(ruta);
    expect(Buffer.compare(bytes, PDF)).toBe(0);
    expect(descarga.suggestedFilename()).toBe("prueba.pdf");

    await dialogo.getByRole("button", { name: "Eliminar" }).click();
    await expect(dialogo.getByText("Documento eliminado.")).toBeVisible();
    await dialogo.locator(".modal__pie").getByRole("button", { name: "Cerrar" }).click();
  });

  await test.step("el administrador recibe el conflicto al borrar un paciente con historial", async () => {
    await cerrarSesion(page);
    await iniciarSesion(page, ADMIN);

    await page
      .locator(".barra-lateral__nav")
      .getByRole("link", { name: "Pacientes", exact: true })
      .click();
    await expect(page.getByRole("heading", { name: "Fichas de pacientes" })).toBeVisible();

    await page.locator("#paciente-filtro-rut").fill(RUT_PRUEBA);
    await page.getByRole("button", { name: "Buscar" }).click();

    const fila = page.getByRole("row", { name: /Prueba Navegador/ });
    await expect(fila).toBeVisible();
    await fila.getByRole("button", { name: "Eliminar" }).click();

    const dialogo = page.getByRole("dialog");
    await dialogo.getByRole("button", { name: "Eliminar" }).click();
    await expect(
      page.locator(".modal-fondo .alerta--error").filter({ hasText: /historial/i }),
    ).toBeVisible();
  });

  expect(errores, `Errores detectados en el navegador:\n${errores.join("\n")}`).toEqual([]);
});
