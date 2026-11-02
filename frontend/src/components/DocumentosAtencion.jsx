import { useCallback, useEffect, useRef, useState } from "react";

import { descargar, pedir } from "../api.js";
import { useAuth } from "../auth.jsx";
import {
  Alerta,
  Cargando,
  Insignia,
  Vacio,
} from "./Comunes.jsx";
import { etiquetaTipoMime, formatearFechaHora, formatearTamano } from "../formato.js";

const MAXIMO_BYTES = 10 * 1024 * 1024;

export default function DocumentosAtencion({ pacienteRut, idAtencion, puedeSubir }) {
  const { usuario } = useAuth();
  const [documentos, setDocumentos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [archivo, setArchivo] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [recarga, setRecarga] = useState(0);
  const entradaArchivo = useRef(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const datos = await pedir(
        `/api/v1/documentos?paciente_rut=${encodeURIComponent(pacienteRut)}&per_page=100`,
      );
      setDocumentos(datos.items.filter((item) => item.id_atencion === idAtencion));
      setError("");
    } catch (fallo) {
      setError(fallo.message);
    } finally {
      setCargando(false);
    }
  }, [pacienteRut, idAtencion]);

  useEffect(() => {
    cargar();
  }, [cargar, recarga]);

  const subir = async (evento) => {
    evento.preventDefault();
    setError("");
    setAviso("");

    if (!archivo) {
      setError("Seleccione un archivo PDF, JPEG o PNG.");
      return;
    }
    if (archivo.size > MAXIMO_BYTES) {
      setError("El archivo supera el máximo permitido de 10 MB.");
      return;
    }

    const datos = new FormData();
    datos.append("paciente_rut", pacienteRut);
    datos.append("id_atencion", idAtencion);
    datos.append("archivo", archivo);

    setSubiendo(true);
    try {
      await pedir("/api/v1/documentos", { metodo: "POST", cuerpo: datos });
      setAviso("Documento adjuntado.");
      setArchivo(null);
      if (entradaArchivo.current) entradaArchivo.current.value = "";
      setRecarga((valor) => valor + 1);
    } catch (fallo) {
      setError(fallo.message);
    } finally {
      setSubiendo(false);
    }
  };

  const bajar = async (documento) => {
    setError("");
    try {
      await descargar(
        `/api/v1/documentos/${documento.id_documento}/archivo`,
        documento.nombre_original,
      );
    } catch (fallo) {
      setError(fallo.message);
    }
  };

  const eliminar = async (documento) => {
    if (!window.confirm(`¿Eliminar el documento "${documento.nombre_original}"?`)) return;
    setError("");
    try {
      await pedir(`/api/v1/documentos/${documento.id_documento}`, { metodo: "DELETE" });
      setAviso("Documento eliminado.");
      setRecarga((valor) => valor + 1);
    } catch (fallo) {
      setError(fallo.message);
    }
  };

  return (
    <div className="documentos-atencion">
      <div className="panel__cabecera">
        <h3>Documentos de esta atención</h3>
      </div>

      <Alerta tipo="ok" onCerrar={() => setAviso("")}>
        {aviso}
      </Alerta>
      <Alerta onCerrar={() => setError("")}>{error}</Alerta>

      {puedeSubir ? (
        <form className="subida" onSubmit={subir}>
          <input
            ref={entradaArchivo}
            type="file"
            accept="application/pdf,image/jpeg,image/png,.pdf,.jpg,.jpeg,.png"
            onChange={(evento) => setArchivo(evento.target.files?.[0] ?? null)}
          />
          <button type="submit" className="boton boton--pequeno" disabled={subiendo}>
            {subiendo ? "Subiendo…" : "Adjuntar"}
          </button>
        </form>
      ) : null}

      {cargando ? (
        <Cargando texto="Cargando documentos…" />
      ) : documentos.length === 0 ? (
        <Vacio>Esta atención no tiene documentos adjuntos.</Vacio>
      ) : (
        <ul className="lista-documentos">
          {documentos.map((documento) => (
            <li key={documento.id_documento} className="lista-documentos__item">
              <div>
                <strong>{documento.nombre_original}</strong>
                <span className="dato-apilado texto-suave">
                  <Insignia tono="neutro">{etiquetaTipoMime(documento.tipo_mime)}</Insignia>{" "}
                  {formatearTamano(documento.tamano_bytes)} ·{" "}
                  {formatearFechaHora(documento.fecha_creacion)} · subido por{" "}
                  {documento.subido_por_rut}
                </span>
              </div>
              <div className="acciones-fila">
                <button
                  type="button"
                  className="boton boton--secundario boton--pequeno"
                  onClick={() => bajar(documento)}
                >
                  Descargar
                </button>
                {documento.subido_por_rut === usuario?.rut ? (
                  <button
                    type="button"
                    className="boton boton--peligro boton--pequeno"
                    onClick={() => eliminar(documento)}
                  >
                    Eliminar
                  </button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
