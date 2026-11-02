import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { descargar, pedir } from "../api.js";
import { useAuth } from "../auth.jsx";
import BuscadorRut from "../components/BuscadorRut.jsx";
import {
  Alerta,
  Campo,
  Cargando,
  Insignia,
  Paginacion,
  Vacio,
} from "../components/Comunes.jsx";
import {
  etiquetaTipoMime,
  formatearFechaHora,
  formatearTamano,
} from "../formato.js";

const MAXIMO_BYTES = 10 * 1024 * 1024;
const TIPOS = ["application/pdf", "image/jpeg", "image/png"];

export default function Documentos() {
  const { usuario } = useAuth();
  const [parametros] = useSearchParams();
  const pacienteParam = parametros.get("paciente") ?? "";

  const [borrador, setBorrador] = useState({ paciente_rut: pacienteParam });
  const [filtros, setFiltros] = useState({ paciente_rut: pacienteParam });
  const [pagina, setPagina] = useState(1);
  const [datos, setDatos] = useState({ items: [], total: 0, pages: 1 });
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [recarga, setRecarga] = useState(0);
  const [mapaAtenciones, setMapaAtenciones] = useState({});

  const [subida, setSubida] = useState({
    paciente_rut: pacienteParam,
    paciente_nombre: "",
    id_atencion: "",
  });
  const [atenciones, setAtenciones] = useState([]);
  const [cargandoAtenciones, setCargandoAtenciones] = useState(false);
  const [archivo, setArchivo] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [errorSubida, setErrorSubida] = useState("");
  const [avisoSubida, setAvisoSubida] = useState("");
  const entradaArchivo = useRef(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const params = new URLSearchParams({ page: String(pagina), per_page: "20" });
      if (filtros.paciente_rut) params.set("paciente_rut", filtros.paciente_rut);

      setDatos(await pedir(`/api/v1/documentos?${params}`));
      setError("");
    } catch (fallo) {
      setError(fallo.message);
    } finally {
      setCargando(false);
    }
  }, [filtros, pagina]);

  useEffect(() => {
    cargar();
  }, [cargar, recarga]);

  useEffect(() => {
    let activo = true;
    pedir("/api/v1/atenciones?per_page=100")
      .then((respuesta) => {
        if (!activo) return;
        setMapaAtenciones(
          Object.fromEntries(
            respuesta.items.map((atencion) => [atencion.id_atencion, atencion]),
          ),
        );
      })
      .catch(() => {
        if (activo) setMapaAtenciones({});
      });
    return () => {
      activo = false;
    };
  }, [recarga]);

  useEffect(() => {
    if (!pacienteParam) return;
    setBorrador((valor) => ({ ...valor, paciente_rut: pacienteParam }));
    setFiltros((valor) => ({ ...valor, paciente_rut: pacienteParam }));
    setSubida((valor) => ({ ...valor, paciente_rut: pacienteParam }));
    setPagina(1);
  }, [pacienteParam]);

  useEffect(() => {
    let activo = true;
    const rut = subida.paciente_rut.trim();

    if (rut.length < 2) {
      setAtenciones([]);
      setCargandoAtenciones(false);
      return undefined;
    }

    setCargandoAtenciones(true);
    const temporizador = setTimeout(async () => {
      try {
        const respuesta = await pedir(
          `/api/v1/atenciones?paciente_rut=${encodeURIComponent(rut)}&per_page=100`,
        );
        if (activo) setAtenciones(respuesta.items);
      } catch {
        if (activo) setAtenciones([]);
      } finally {
        if (activo) setCargandoAtenciones(false);
      }
    }, 350);

    return () => {
      activo = false;
      clearTimeout(temporizador);
    };
  }, [subida.paciente_rut]);

  const aplicarFiltros = (evento) => {
    evento.preventDefault();
    setPagina(1);
    setFiltros({ ...borrador });
  };

  const subir = async (evento) => {
    evento.preventDefault();
    setErrorSubida("");
    setAvisoSubida("");

    if (!subida.paciente_rut.trim()) {
      setErrorSubida("Indique el paciente al que pertenece el documento.");
      return;
    }
    if (!archivo) {
      setErrorSubida("Seleccione un archivo PDF, JPEG o PNG.");
      return;
    }
    if (!TIPOS.includes(archivo.type) && archivo.type) {
      setErrorSubida("Solo se permiten documentos PDF, JPEG o PNG.");
      return;
    }
    if (archivo.size > MAXIMO_BYTES) {
      setErrorSubida("El archivo supera el máximo permitido de 10 MB.");
      return;
    }

    const cuerpo = new FormData();
    cuerpo.append("paciente_rut", subida.paciente_rut.trim());
    if (subida.id_atencion) cuerpo.append("id_atencion", subida.id_atencion);
    cuerpo.append("archivo", archivo);

    setSubiendo(true);
    try {
      await pedir("/api/v1/documentos", { metodo: "POST", cuerpo });
      setAvisoSubida("Documento subido correctamente.");
      setArchivo(null);
      if (entradaArchivo.current) entradaArchivo.current.value = "";
      setRecarga((valor) => valor + 1);
    } catch (fallo) {
      setErrorSubida(fallo.message);
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

  const detalleAtencion = (id) => {
    if (!id) return "Sin atención";
    const atencion = mapaAtenciones[id];
    return atencion ? formatearFechaHora(atencion.fecha_atencion) : `${id.slice(0, 8)}…`;
  };

  return (
    <div className="pila">
      <div className="pagina__cabecera">
        <div>
          <h2>Documentos privados</h2>
          <p className="texto-suave">
            Archivos PDF, JPEG o PNG de hasta 10 MB. Solo se muestran los documentos
            que usted puede consultar.
          </p>
        </div>
      </div>

      <section className="panel">
        <div className="panel__cabecera">
          <h2>Subir un documento</h2>
        </div>

        <Alerta tipo="ok" onCerrar={() => setAvisoSubida("")}>
          {avisoSubida}
        </Alerta>
        <Alerta onCerrar={() => setErrorSubida("")}>{errorSubida}</Alerta>

        <form className="formulario" onSubmit={subir}>
          <div className="formulario__grilla">
            <Campo
              etiqueta="Paciente"
              htmlFor="documento-paciente"
              requerido
              ayuda={
                subida.paciente_nombre
                  ? `Seleccionado: ${subida.paciente_nombre}`
                  : "Escriba el RUT y elija una coincidencia."
              }
            >
              <BuscadorRut
                id="documento-paciente"
                valor={subida.paciente_rut}
                onCambio={(rut, item) =>
                  setSubida((valor) => ({
                    ...valor,
                    paciente_rut: rut,
                    paciente_nombre: item ? `${item.nombres} ${item.apellidos}` : "",
                    id_atencion: "",
                  }))
                }
              />
            </Campo>

            <Campo
              etiqueta="Atención (opcional)"
              htmlFor="documento-atencion"
              ayuda={
                cargandoAtenciones
                  ? "Buscando atenciones…"
                  : "Puede adjuntarlo solo al paciente, sin atención."
              }
            >
              <select
                id="documento-atencion"
                value={subida.id_atencion}
                onChange={(evento) =>
                  setSubida({ ...subida, id_atencion: evento.target.value })
                }
                disabled={atenciones.length === 0}
              >
                <option value="">Sin atención asociada</option>
                {atenciones.map((atencion) => (
                  <option key={atencion.id_atencion} value={atencion.id_atencion}>
                    {formatearFechaHora(atencion.fecha_atencion)} · {atencion.motivo}
                  </option>
                ))}
              </select>
            </Campo>
          </div>

          <div className="subida">
            <input
              ref={entradaArchivo}
              type="file"
              accept="application/pdf,image/jpeg,image/png,.pdf,.jpg,.jpeg,.png"
              onChange={(evento) => setArchivo(evento.target.files?.[0] ?? null)}
            />
            <button type="submit" className="boton" disabled={subiendo}>
              {subiendo ? "Subiendo…" : "Subir documento"}
            </button>
          </div>
        </form>
      </section>

      <Alerta tipo="ok" onCerrar={() => setAviso("")}>
        {aviso}
      </Alerta>
      <Alerta onCerrar={() => setError("")}>{error}</Alerta>

      <form className="panel filtros" onSubmit={aplicarFiltros}>
        <Campo etiqueta="Paciente (RUT)" htmlFor="documento-filtro">
          <input
            id="documento-filtro"
            type="text"
            value={borrador.paciente_rut}
            placeholder="Búsqueda parcial"
            onChange={(evento) =>
              setBorrador({ ...borrador, paciente_rut: evento.target.value })
            }
          />
        </Campo>
        <div className="filtros__acciones">
          <button type="submit" className="boton">
            Buscar
          </button>
        </div>
      </form>

      <section className="panel">
        {cargando ? (
          <Cargando />
        ) : datos.items.length === 0 ? (
          <Vacio>No hay documentos para mostrar.</Vacio>
        ) : (
          <>
            <div className="tabla-envoltura">
              <table className="tabla">
                <thead>
                  <tr>
                    <th>Archivo</th>
                    <th>Paciente</th>
                    <th>Atención</th>
                    <th>Subido por</th>
                    <th>Fecha</th>
                    <th aria-label="Acciones" />
                  </tr>
                </thead>
                <tbody>
                  {datos.items.map((documento) => (
                    <tr key={documento.id_documento}>
                      <td>
                        <strong>{documento.nombre_original}</strong>
                        <span className="dato-apilado texto-suave">
                          <Insignia tono="neutro">
                            {etiquetaTipoMime(documento.tipo_mime)}
                          </Insignia>{" "}
                          {formatearTamano(documento.tamano_bytes)}
                        </span>
                      </td>
                      <td className="mono">{documento.paciente_rut}</td>
                      <td>{detalleAtencion(documento.id_atencion)}</td>
                      <td className="mono">{documento.subido_por_rut}</td>
                      <td>{formatearFechaHora(documento.fecha_creacion)}</td>
                      <td className="tabla__acciones">
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
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Paginacion
              pagina={datos.page}
              paginas={datos.pages}
              total={datos.total}
              onCambiar={setPagina}
            />
          </>
        )}
      </section>
    </div>
  );
}
