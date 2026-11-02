import { Link, Route, Routes } from "react-router-dom";

import { RequiereRol, RequiereSesion } from "./auth.jsx";
import Layout from "./components/Layout.jsx";
import Atenciones from "./pages/Atenciones.jsx";
import Citas from "./pages/Citas.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Documentos from "./pages/Documentos.jsx";
import Login from "./pages/Login.jsx";
import Pacientes from "./pages/Pacientes.jsx";
import Profesionales from "./pages/Profesionales.jsx";
import Usuarios from "./pages/Usuarios.jsx";

function NoEncontrada() {
  return (
    <section className="panel">
      <div className="panel__cabecera">
        <h2>Página no encontrada</h2>
      </div>
      <p className="texto-suave">La dirección solicitada no existe en el sistema.</p>
      <p>
        <Link to="/">Volver al resumen</Link>
      </p>
    </section>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        element={
          <RequiereSesion>
            <Layout />
          </RequiereSesion>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="citas" element={<Citas />} />
        <Route path="atenciones" element={<Atenciones />} />
        <Route path="pacientes" element={<Pacientes />} />
        <Route path="profesionales" element={<Profesionales />} />
        <Route path="documentos" element={<Documentos />} />
        <Route
          path="usuarios"
          element={
            <RequiereRol rol="administrador">
              <Usuarios />
            </RequiereRol>
          }
        />
        <Route path="*" element={<NoEncontrada />} />
      </Route>
    </Routes>
  );
}
