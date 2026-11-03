import { defineConfig } from "@playwright/test";

/**
 * Las pruebas usan el Chrome instalado en el equipo por defecto.
 * Para usar Edge u otro canal: PLAYWRIGHT_CHANNEL=msedge
 * Para usar el Chromium de Playwright: npx playwright install chromium
 * y luego PLAYWRIGHT_CHANNEL=chromium.
 */
export default defineConfig({
  testDir: "./pruebas",
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
  ],
  use: {
    baseURL: process.env.DISS_E2E_BASE_URL ?? "http://localhost:5173",
    channel: process.env.PLAYWRIGHT_CHANNEL ?? "chrome",
    headless: true,
    acceptDownloads: true,
    viewport: { width: 1440, height: 960 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
