import { useEffect, useRef, useState } from "react";

import { pedir } from "../api.js";
import { nombreCompleto } from "../formato.js";

/**
 * Entrada de RUT con sugerencias obtenidas de la API.
 * El valor que maneja el formulario es siempre el RUT; el nombre solo se
 * muestra en la lista de sugerencias.
 */
export default function BuscadorRut({
  id = "buscador-rut",
  recurso = "pacientes",
  valor,
  onCambio,
  placeholder = "Ej.: 12.345.678-9",
  deshabilitado = false,
}) {
  const [opciones, setOpciones] = useState([]);
  const [abierto, setAbierto] = useState(false);
  const [buscando, setBuscando] = useState(false);
  const [error, setError] = useState("");
  const contenedor = useRef(null);

  useEffect(() => {
    const texto = (valor ?? "").trim();
    if (texto.length < 2) {
      setOpciones([]);
      setBuscando(false);
      return undefined;
    }

    let cancelado = false;
    setBuscando(true);

    const temporizador = setTimeout(async () => {
      try {
        const datos = await pedir(
          `/api/v1/${recurso}?rut=${encodeURIComponent(texto)}&activo=true&per_page=6`,
        );
        if (!cancelado) {
          setOpciones(datos.items);
          setError("");
        }
      } catch (fallo) {
        if (!cancelado) {
          setOpciones([]);
          setError(fallo.message);
        }
      } finally {
        if (!cancelado) setBuscando(false);
      }
    }, 320);

    return () => {
      cancelado = true;
      clearTimeout(temporizador);
    };
  }, [valor, recurso]);

  useEffect(() => {
    const alHacerClicFuera = (evento) => {
      if (contenedor.current && !contenedor.current.contains(evento.target)) {
        setAbierto(false);
      }
    };
    document.addEventListener("mousedown", alHacerClicFuera);
    return () => document.removeEventListener("mousedown", alHacerClicFuera);
  }, []);

  const elegir = (item) => {
    onCambio(item.rut, item);
    setAbierto(false);
  };

  const mostrarLista = abierto && (buscando || opciones.length > 0 || error);

  return (
    <div className="buscador" ref={contenedor}>
      <input
        id={id}
        type="text"
        value={valor ?? ""}
        placeholder={placeholder}
        autoComplete="off"
        disabled={deshabilitado}
        onChange={(evento) => {
          onCambio(evento.target.value, null);
          setAbierto(true);
        }}
        onFocus={() => setAbierto(true)}
      />

      {mostrarLista ? (
        <div className="buscador__opciones" role="listbox" aria-label="Sugerencias">
          {buscando ? <p className="buscador__estado">Buscando…</p> : null}
          {!buscando && error ? (
            <p className="buscador__estado buscador__estado--error">{error}</p>
          ) : null}
          {!buscando && !error && opciones.length === 0 ? (
            <p className="buscador__estado">Sin coincidencias activas.</p>
          ) : null}
          {opciones.map((item) => (
            <button
              key={item.rut}
              type="button"
              role="option"
              aria-selected="false"
              className="buscador__opcion"
              onMouseDown={(evento) => {
                evento.preventDefault();
                elegir(item);
              }}
            >
              <strong>{item.rut}</strong>
              <span>{nombreCompleto(item)}</span>
              {item.especialidad ? <em>{item.especialidad}</em> : null}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
