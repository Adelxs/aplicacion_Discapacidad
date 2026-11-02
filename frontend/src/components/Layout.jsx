import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth.jsx";
import { etiquetaRol } from "../formato.js";
import { InsigniaRol } from "./Comunes.jsx";

const ENLACES = [
  { ruta: "/", texto: "Resumen", soloAdmin: false },
  { ruta: "/citas", texto: "Citas", soloAdmin: false },
  { ruta: "/atenciones", texto: "Atenciones", soloAdmin: false },
  { ruta: "/pacientes", texto: "Pacientes", soloAdmin: false },
  { ruta: "/profesionales", texto: "Profesionales", soloAdmin: false },
  { ruta: "/documentos", texto: "Documentos", soloAdmin: false },
  { ruta: "/usuarios", texto: "Usuarios", soloAdmin: true },
];

const TITULOS = {
  "/": "Resumen general",
  "/citas": "Citas y agenda",
  "/atenciones": "Atenciones",
  "/pacientes": "Pacientes",
  "/profesionales": "Profesionales",
  "/documentos": "Documentos",
  "/usuarios": "Usuarios del sistema",
};

function iniciales(usuario) {
  if (!usuario) return "?";
  return `${usuario.nombres?.[0] ?? ""}${usuario.apellidos?.[0] ?? ""}`.toUpperCase();
}

export default function Layout() {
  const { usuario, esAdministrador, cerrarSesion } = useAuth();
  const navegar = useNavigate();
  const ubicacion = useLocation();
  const [menuAbierto, setMenuAbierto] = useState(false);

  const enlaces = ENLACES.filter((enlace) => !enlace.soloAdmin || esAdministrador);
  const titulo = TITULOS[ubicacion.pathname] ?? "Sistema municipal";

  const salir = () => {
    cerrarSesion();
    navegar("/login", { replace: true });
  };

  return (
    <div className="app">
      <aside className={`barra-lateral ${menuAbierto ? "barra-lateral--abierta" : ""}`}>
        <div className="barra-lateral__marca">
          <span className="barra-lateral__escudo" aria-hidden="true">
            S
          </span>
          <div>
            <strong>Citas Municipales</strong>
            <span>Gestión clínica</span>
          </div>
        </div>

        <nav className="barra-lateral__nav" aria-label="Navegación principal">
          {enlaces.map((enlace) => (
            <NavLink
              key={enlace.ruta}
              to={enlace.ruta}
              end={enlace.ruta === "/"}
              className={({ isActive }) =>
                `nav-enlace ${isActive ? "nav-enlace--activo" : ""}`
              }
              onClick={() => setMenuAbierto(false)}
            >
              {enlace.texto}
            </NavLink>
          ))}
        </nav>

        <div className="barra-lateral__pie">
          <div className="usuario">
            <span className="usuario__avatar" aria-hidden="true">
              {iniciales(usuario)}
            </span>
            <div className="usuario__datos">
              <strong>
                {usuario?.nombres} {usuario?.apellidos}
              </strong>
              <span>{usuario?.rut}</span>
              <InsigniaRol rol={usuario?.rol} />
            </div>
          </div>
          <button type="button" className="boton boton--secundario boton--bloque" onClick={salir}>
            Cerrar sesión
          </button>
        </div>
      </aside>

      <div className="contenido">
        <header className="barra-superior">
          <button
            type="button"
            className="menu-movil"
            onClick={() => setMenuAbierto((abierto) => !abierto)}
            aria-expanded={menuAbierto}
            aria-label="Abrir o cerrar navegación"
          >
            ☰
          </button>
          <div>
            <p className="barra-superior__etiqueta">{etiquetaRol(usuario?.rol)}</p>
            <h1>{titulo}</h1>
          </div>
        </header>

        <main className="pagina">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
