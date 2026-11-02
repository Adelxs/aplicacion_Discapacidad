import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { pedir } from "../api.js";
import { useAuth } from "../auth.jsx";
import DocumentosAtencion from "../components/DocumentosAtencion.jsx";
import {
  Alerta,
  Campo,
  Cargando,
  DetalleItem,
  DetalleLista,
  Modal,
  Paginacion,
  Vacio,
} from "../components/Comunes.jsx";
import { formatearFechaHora } from "../formato.js";

export default function Atenciones() {
  const { usuario, esAdministrador } = useAuth();
  const [borrador, setBorrador] = useState({ paciente_rut: "", desde: "", hasta: "" });
  const [filtros, setFiltros] = useState({ paciente_rut: "", desde: "", hasta: "" });
  const [pagina, setPagina] = useState(1);
  const [datos, setDatos] = useState({ items: [], total: 0, pages: 1 });
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [recarga, setRecarga] = useState(0);

  const [detalle, setDetalle] = useState(null);
  const [editando, setEditando] = useState(false);
  const [form, setForm] = useState({ motivo: "", registro_clinico: "" });
  const [errorModal, setErrorModal] = useState("");
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const params = new URLSearchParams({ page: String(pagina), per_page: "20" });
      if (filtros.paciente_rut) params.set("paciente_rut", filtros.paciente_rut);
      if (filtros.desde) params.set("desde", filtros.desde);
      if (filtros.hasta) params.set("hasta", filtros.hasta);

      setDatos(await pedir(`/api/v1/atenciones?${params}`));
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

  const aplicarFiltros = (evento) => {
    evento.preventDefault();
    setPagina(1);
    setFiltros({ ...borrador });
  };

  const abrirDetalle = (atencion) => {
    setDetalle(atencion);
    setForm({ motivo: atencion.motivo, registro_clinico: atencion.registro_clinico });
    setEditando(false);
    setErrorModal("");
  };

  const guardar = async (evento) => {
    evento.preventDefault();
    setGuardando(true);
    setErrorModal("");
    try {
      const actualizada = await pedir(`/api/v1/atenciones/${detalle.id_atencion}`, {
        metodo: "PATCH",
        cuerpo: { motivo: form.motivo, registro_clinico: form.registro_clinico },
      });
      setDetalle(actualizada);
      setEditando(false);
      setAviso("Registro clínico corregido.");
      setRecarga((valor) => valor + 1);
    } catch (fallo) {
      setErrorModal(fallo.message);
    } finally {
      setGuardando(false);
    }
  };

  const esDueno = detalle?.profesional_rut === usuario?.rut;

  return (
    <div className="pila">
      <div className="pagina__cabecera">
        <div>
          <h2>Registros de atención</h2>
          <p className="texto-suave">
            {esAdministrador
              ? "Consulte los registros clínicos de todo el sistema."
              : "Consulte sus atenciones y corrija sus propios registros."}
          </p>
        </div>
        {!esAdministrador ? (
          <Link className="boton" to="/citas">
            Ir a la agenda
          </Link>
        ) : null}
      </div>

      <Alerta tipo="ok" onCerrar={() => setAviso("")}>
        {aviso}
      </Alerta>
      <Alerta onCerrar={() => setError("")}>{error}</Alerta>

      <form className="panel filtros" onSubmit={aplicarFiltros}>
        <Campo etiqueta="Paciente (RUT)" htmlFor="atencion-filtro-paciente">
          <input
            id="atencion-filtro-paciente"
            type="text"
            value={borrador.paciente_rut}
            placeholder="Búsqueda parcial"
            onChange={(evento) =>
              setBorrador({ ...borrador, paciente_rut: evento.target.value })
            }
          />
        </Campo>
        <Campo etiqueta="Desde" htmlFor="atencion-filtro-desde">
          <input
            id="atencion-filtro-desde"
            type="date"
            value={borrador.desde}
            onChange={(evento) => setBorrador({ ...borrador, desde: evento.target.value })}
          />
        </Campo>
        <Campo etiqueta="Hasta" htmlFor="atencion-filtro-hasta">
          <input
            id="atencion-filtro-hasta"
            type="date"
            value={borrador.hasta}
            onChange={(evento) => setBorrador({ ...borrador, hasta: evento.target.value })}
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
          <Vacio />
        ) : (
          <>
            <div className="tabla-envoltura">
              <table className="tabla">
                <thead>
                  <tr>
                    <th>Fecha de atención</th>
                    <th>Paciente</th>
                    <th>Profesional</th>
                    <th>Motivo</th>
                    <th>Registrada por</th>
                    <th aria-label="Acciones" />
                  </tr>
                </thead>
                <tbody>
                  {datos.items.map((atencion) => (
                    <tr key={atencion.id_atencion}>
                      <td>{formatearFechaHora(atencion.fecha_atencion)}</td>
                      <td className="mono">{atencion.paciente_rut}</td>
                      <td className="mono">{atencion.profesional_rut}</td>
                      <td>{atencion.motivo}</td>
                      <td className="mono">{atencion.creado_por_rut}</td>
                      <td className="tabla__acciones">
                        <button
                          type="button"
                          className="boton boton--secundario boton--pequeno"
                          onClick={() => abrirDetalle(atencion)}
                        >
                          Ver ficha
                        </button>
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

      {detalle ? (
        <Modal
          titulo={`Atención del ${formatearFechaHora(detalle.fecha_atencion)}`}
          onCerrar={() => setDetalle(null)}
          ancho="ancho"
        >
          <Alerta tipo="ok" onCerrar={() => setAviso("")}>
            {aviso}
          </Alerta>
          <Alerta onCerrar={() => setErrorModal("")}>{errorModal}</Alerta>

          {editando ? (
            <form className="formulario" onSubmit={guardar}>
              <Campo etiqueta="Motivo" htmlFor="atencion-edit-motivo" requerido>
                <input
                  id="atencion-edit-motivo"
                  type="text"
                  maxLength={500}
                  value={form.motivo}
                  onChange={(evento) => setForm({ ...form, motivo: evento.target.value })}
                  required
                />
              </Campo>
              <Campo etiqueta="Registro clínico" htmlFor="atencion-edit-registro" requerido>
                <textarea
                  id="atencion-edit-registro"
                  rows={10}
                  maxLength={10000}
                  value={form.registro_clinico}
                  onChange={(evento) =>
                    setForm({ ...form, registro_clinico: evento.target.value })
                  }
                  required
                />
              </Campo>
              <div className="modal__pie">
                <button
                  type="button"
                  className="boton boton--secundario"
                  onClick={() => setEditando(false)}
                  disabled={guardando}
                >
                  Cancelar
                </button>
                <button type="submit" className="boton" disabled={guardando}>
                  {guardando ? "Guardando…" : "Guardar corrección"}
                </button>
              </div>
            </form>
          ) : (
            <>
              <DetalleLista>
                <DetalleItem etiqueta="Paciente">{detalle.paciente_rut}</DetalleItem>
                <DetalleItem etiqueta="Profesional">{detalle.profesional_rut}</DetalleItem>
                <DetalleItem etiqueta="Cita">{detalle.id_cita}</DetalleItem>
                <DetalleItem etiqueta="Fecha de atención">
                  {formatearFechaHora(detalle.fecha_atencion)}
                </DetalleItem>
                <DetalleItem etiqueta="Motivo">{detalle.motivo}</DetalleItem>
              </DetalleLista>

              <div className="registro">
                <h3>Registro clínico</h3>
                <p>{detalle.registro_clinico}</p>
              </div>

              <DetalleLista>
                <DetalleItem etiqueta="Registrada por">{detalle.creado_por_rut}</DetalleItem>
                <DetalleItem etiqueta="Fecha de creación">
                  {formatearFechaHora(detalle.fecha_creacion)}
                </DetalleItem>
              </DetalleLista>

              <DocumentosAtencion
                pacienteRut={detalle.paciente_rut}
                idAtencion={detalle.id_atencion}
                puedeSubir={esAdministrador || esDueno}
              />

              <div className="modal__pie">
                <button
                  type="button"
                  className="boton boton--secundario"
                  onClick={() => setDetalle(null)}
                >
                  Cerrar
                </button>
                {esDueno ? (
                  <button type="button" className="boton" onClick={() => setEditando(true)}>
                    Corregir registro
                  </button>
                ) : null}
              </div>
            </>
          )}
        </Modal>
      ) : null}
    </div>
  );
}
