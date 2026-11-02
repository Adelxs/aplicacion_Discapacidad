import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { pedir } from "../api.js";
import { useAuth } from "../auth.jsx";
import { Alerta } from "../components/Comunes.jsx";

export default function Login() {
  const { sesion, iniciarSesion } = useAuth();
  const navegar = useNavigate();
  const ubicacion = useLocation();
  const [rut, setRut] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  if (sesion) {
    return <Navigate to="/" replace />;
  }

  const enviar = async (evento) => {
    evento.preventDefault();
    setError("");
    setEnviando(true);
    try {
      const datos = await pedir("/api/v1/auth/login", {
        metodo: "POST",
        cuerpo: { rut, password },
      });
      iniciarSesion(datos);
      navegar(ubicacion.state?.desde ?? "/", { replace: true });
    } catch (fallo) {
      setError(fallo.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="login">
      <div className="login__presentacion">
        <span className="login__escudo" aria-hidden="true">
          S
        </span>
        <p className="login__etiqueta">Municipalidad · Salud</p>
        <h1>Sistema Municipal de Citas y Atenciones</h1>
        <p>
          Acceso reservado para funcionarios autorizados. La información clínica
          y los documentos adjuntos son confidenciales.
        </p>
      </div>

      <form className="login__tarjeta" onSubmit={enviar}>
        <div>
          <h2>Iniciar sesión</h2>
          <p className="texto-suave">Ingrese con su RUT y contraseña institucional.</p>
        </div>

        <Alerta>{error}</Alerta>

        <div className="campo">
          <label htmlFor="rut">RUT</label>
          <input
            id="rut"
            name="rut"
            type="text"
            value={rut}
            onChange={(evento) => setRut(evento.target.value)}
            placeholder="12.345.678-9"
            autoComplete="username"
            autoFocus
            required
          />
        </div>

        <div className="campo">
          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            name="password"
            type="password"
            value={password}
            onChange={(evento) => setPassword(evento.target.value)}
            autoComplete="current-password"
            required
          />
        </div>

        <button type="submit" className="boton boton--bloque" disabled={enviando}>
          {enviando ? "Ingresando…" : "Ingresar"}
        </button>

        {ubicacion.state?.desde ? (
          <p className="login__aviso">Debe iniciar sesión para continuar.</p>
        ) : null}

        <p className="login__pie">Sistema interno · MVP</p>
      </form>
    </div>
  );
}
