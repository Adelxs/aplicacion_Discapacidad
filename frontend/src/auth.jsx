import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { configurarToken } from "./api.js";

const CLAVE_SESION = "diss_sesion";
const AuthContext = createContext(null);

function leerSesion() {
  try {
    const guardada = window.sessionStorage.getItem(CLAVE_SESION);
    return guardada ? JSON.parse(guardada) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [sesion, setSesion] = useState(() => {
    const guardada = leerSesion();
    configurarToken(guardada?.token ?? null);
    return guardada;
  });

  const iniciarSesion = useCallback((datos) => {
    const nueva = { token: datos.access_token, usuario: datos.usuario };
    window.sessionStorage.setItem(CLAVE_SESION, JSON.stringify(nueva));
    configurarToken(nueva.token);
    setSesion(nueva);
  }, []);

  const cerrarSesion = useCallback(() => {
    window.sessionStorage.removeItem(CLAVE_SESION);
    configurarToken(null);
    setSesion(null);
  }, []);

  useEffect(() => {
    const alExpirar = () => cerrarSesion();
    window.addEventListener("diss:sesion-expirada", alExpirar);
    return () => window.removeEventListener("diss:sesion-expirada", alExpirar);
  }, [cerrarSesion]);

  const valor = useMemo(
    () => ({
      sesion,
      usuario: sesion?.usuario ?? null,
      iniciarSesion,
      cerrarSesion,
      esAdministrador: sesion?.usuario?.rol === "administrador",
      esProfesional: sesion?.usuario?.rol === "profesional",
    }),
    [sesion, iniciarSesion, cerrarSesion],
  );

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const contexto = useContext(AuthContext);
  if (!contexto) {
    throw new Error("useAuth debe usarse dentro de AuthProvider.");
  }
  return contexto;
}

export function RequiereSesion({ children }) {
  const { sesion } = useAuth();
  const ubicacion = useLocation();

  if (!sesion) {
    return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />;
  }
  return children;
}

export function RequiereRol({ rol, children }) {
  const { usuario } = useAuth();
  if (usuario?.rol !== rol) {
    return <Navigate to="/" replace />;
  }
  return children;
}
