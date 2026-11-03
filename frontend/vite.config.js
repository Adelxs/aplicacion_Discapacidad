import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Hosts permitidos por el servidor de Vite. En local no hace falta nada; en
 * Render se define el dominio público del servicio. Se puede ampliar con
 * VITE_ALLOWED_HOSTS="host1,host2" sin modificar el código.
 */
const allowedHosts = (
  process.env.VITE_ALLOWED_HOSTS ?? "aplicacion-discapacidad.onrender.com"
)
  .split(",")
  .map((host) => host.trim())
  .filter(Boolean);

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    allowedHosts,
    watch: {
      // Necesario para detectar cambios con bind mounts en Windows/macOS.
      usePolling: true,
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    allowedHosts,
  },
});
