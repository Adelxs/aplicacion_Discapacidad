import { useCallback, useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function consultar(ruta) {
  const respuesta = await fetch(`${API_URL}${ruta}`, {
    headers: { Accept: "application/json" },
  });
  const cuerpo = await respuesta.json().catch(() => null);

  if (!respuesta.ok) {
    throw new Error(cuerpo?.error?.mensaje ?? `Error HTTP ${respuesta.status}`);
  }
  return cuerpo;
}

function TarjetaEstado({ titulo, descripcion, estado, datos }) {
  const etiqueta =
    estado === "ok" ? "Operativo" : estado === "error" ? "Con problemas" : "Verificando";

  return (
    <section className={`tarjeta tarjeta--${estado}`}>
      <div className="tarjeta__cabecera">
        <h2>{titulo}</h2>
        <span className="insignia">{etiqueta}</span>
      </div>
      <p className="tarjeta__descripcion">{descripcion}</p>

      {estado === "error" ? (
        <p className="tarjeta__error" role="alert">
          {datos}
        </p>
      ) : null}

      {estado === "ok" && datos ? (
        <dl className="detalle">
          {Object.entries(datos).map(([clave, valor]) => (
            <div key={clave} className="detalle__fila">
              <dt>{clave.replaceAll("_", " ")}</dt>
              <dd>{String(valor)}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </section>
  );
}

export default function App() {
  const [servicio, setServicio] = useState({ estado: "cargando" });
  const [baseDatos, setBaseDatos] = useState({ estado: "cargando" });
  const [actualizado, setActualizado] = useState(null);

  const verificar = useCallback(async () => {
    setServicio({ estado: "cargando" });
    setBaseDatos({ estado: "cargando" });

    const [saludServicio, saludBaseDatos] = await Promise.allSettled([
      consultar("/api/v1/health"),
      consultar("/api/v1/health/db"),
    ]);

    setServicio(
      saludServicio.status === "fulfilled"
        ? { estado: "ok", datos: saludServicio.value }
        : { estado: "error", datos: saludServicio.reason.message },
    );
    setBaseDatos(
      saludBaseDatos.status === "fulfilled"
        ? { estado: "ok", datos: saludBaseDatos.value }
        : { estado: "error", datos: saludBaseDatos.reason.message },
    );
    setActualizado(new Date().toLocaleTimeString("es-CL"));
  }, []);

  useEffect(() => {
    verificar();
  }, [verificar]);

  return (
    <div className="contenedor">
      <header className="encabezado">
        <p className="encabezado__etiqueta">Etapa 1 · Verificación del entorno</p>
        <h1>Sistema Municipal de Citas y Atenciones</h1>
        <p className="encabezado__texto">
          Comprobación de la conexión entre React, FastAPI y PostgreSQL.
        </p>
      </header>

      <main className="grilla">
        <TarjetaEstado
          titulo="API FastAPI"
          descripcion="Servicio backend que expone la API REST del sistema."
          estado={servicio.estado}
          datos={servicio.estado === "ok" ? servicio.datos : servicio.datos}
        />
        <TarjetaEstado
          titulo="Base de datos PostgreSQL"
          descripcion="Verificación real de consulta contra el contenedor de base de datos."
          estado={baseDatos.estado}
          datos={baseDatos.estado === "ok" ? baseDatos.datos : baseDatos.datos}
        />
      </main>

      <footer className="pie">
        <button type="button" className="boton" onClick={verificar}>
          Volver a verificar
        </button>
        {actualizado ? <span>Última verificación: {actualizado}</span> : null}
        <a href={`${API_URL}/docs`} target="_blank" rel="noreferrer">
          Documentación de la API
        </a>
      </footer>
    </div>
  );
}
