import { useCallback, useEffect, useState } from "react";

import { pedir } from "../api.js";
import { useAuth } from "../auth.jsx";
import BuscadorRut from "../components/BuscadorRut.jsx";
import {
  Alerta,
  Campo,
  Cargando,
  DetalleItem,
  DetalleLista,
  InsigniaEstado,
  Modal,
  Paginacion,
  Vacio,
} from "../components/Comunes.jsx";
import {
  aDatetimeLocal,
  etiquetaEstado,
  formatearFechaHora,
  formatearRango,
} from "../formato.js";

const ESTADOS = ["pendiente", "confirmada", "atendida", "cancelada", "ausente"];

export default function Citas() {
  const { usuario, esAdministrador, esProfesional } = useAuth();
  const [borrador, setBorrador] = useState({
    paciente_rut: "",
    estado: "",
    desde: "",
    hasta: "",
  });
  const [filtros, setFiltros] = useState({
    paciente_rut: "",
    estado: "",
    desde: "",
    hasta: "",
  });
  const [pagina, setPagina] = useState(1);
  const [datos, setDatos] = useState({ items: [], total: 0, pages: 1 });
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [recarga, setRecarga] = useState(0);
  const [accionando, setAccionando] = useState("");

  const [modal, setModal] = useState(null);
  const [errorModal, setErrorModal] = useState("");
  const [guardando, setGuardando] = useState(false);

  const [nuevaCita, setNuevaCita] = useState({
    paciente_rut: "",
    paciente_nombre: "",
    inicio: "",
    fin: "",
    motivo: "",
  });
  const [atencion, setAtencion] = useState({
    fecha_atencion: "",
    motivo: "",
    registro_clinico: "",
  });
  const [observaciones, setObservaciones] = useState("");

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const params = new URLSearchParams({ page: String(pagina), per_page: "20" });
      if (filtros.paciente_rut) params.set("paciente_rut", filtros.paciente_rut);
      if (filtros.estado) params.set("estado", filtros.estado);
      if (filtros.desde) params.set("desde", filtros.desde);
      if (filtros.hasta) params.set("hasta", filtros.hasta);

      setDatos(await pedir(`/api/v1/citas?${params}`));
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

  const cambiarEstado = async (cita, accion, mensaje) => {
    if (accion !== "confirmar") {
      const pregunta =
        accion === "cancelar"
          ? "¿Cancelar esta cita? El horario quedará liberado."
          : "¿Marcar al paciente como ausente? La cita quedará cerrada.";
      if (!window.confirm(pregunta)) return;
    }

    setAccionando(cita.id_cita);
    setError("");
    try {
      await pedir(`/api/v1/citas/${cita.id_cita}/${accion}`, { metodo: "POST" });
      setAviso(mensaje);
      setRecarga((valor) => valor + 1);
    } catch (fallo) {
      setError(fallo.message);
    } finally {
      setAccionando("");
    }
  };

  const abrirCrear = () => {
    setNuevaCita({ paciente_rut: "", paciente_nombre: "", inicio: "", fin: "", motivo: "" });
    setErrorModal("");
    setModal({ tipo: "crear" });
  };

  const crearCita = async (evento) => {
    evento.preventDefault();
    setErrorModal("");

    if (nuevaCita.fin <= nuevaCita.inicio) {
      setErrorModal("La fecha y hora de fin debe ser posterior al inicio.");
      return;
    }

    setGuardando(true);
    try {
      await pedir("/api/v1/citas", {
        metodo: "POST",
        cuerpo: {
          paciente_rut: nuevaCita.paciente_rut,
          fecha_hora_inicio: nuevaCita.inicio,
          fecha_hora_fin: nuevaCita.fin,
          motivo: nuevaCita.motivo,
        },
      });
      setAviso("Cita agendada. Queda pendiente de confirmación.");
      setModal(null);
      setRecarga((valor) => valor + 1);
    } catch (fallo) {
      setErrorModal(fallo.message);
    } finally {
      setGuardando(false);
    }
  };

  const abrirAtencion = (cita) => {
    setAtencion({
      fecha_atencion: aDatetimeLocal(cita.fecha_hora_inicio),
      motivo: cita.motivo,
      registro_clinico: "",
    });
    setErrorModal("");
    setModal({ tipo: "atencion", cita });
  };

  const registrarAtencion = async (evento) => {
    evento.preventDefault();
    setGuardando(true);
    setErrorModal("");
    try {
      await pedir("/api/v1/atenciones", {
        metodo: "POST",
        cuerpo: {
          id_cita: modal.cita.id_cita,
          fecha_atencion: atencion.fecha_atencion,
          motivo: atencion.motivo,
          registro_clinico: atencion.registro_clinico,
        },
      });
      setAviso("Atención registrada. La cita pasó a estado atendida.");
      setModal(null);
      setRecarga((valor) => valor + 1);
    } catch (fallo) {
      setErrorModal(fallo.message);
    } finally {
      setGuardando(false);
    }
  };

  const abrirObservaciones = (cita) => {
    setObservaciones(cita.observaciones_administrativas ?? "");
    setErrorModal("");
    setModal({ tipo: "observaciones", cita });
  };

  const guardarObservaciones = async (evento) => {
    evento.preventDefault();
    setGuardando(true);
    setErrorModal("");
    try {
      await pedir(`/api/v1/citas/${modal.cita.id_cita}/observaciones`, {
        metodo: "PATCH",
        cuerpo: {
          observaciones_administrativas: observaciones.trim() || null,
        },
      });
      setAviso("Observaciones administrativas actualizadas.");
      setModal(null);
      setRecarga((valor) => valor + 1);
    } catch (fallo) {
      setErrorModal(fallo.message);
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="pila">
      <div className="pagina__cabecera">
        <div>
          <h2>Agenda de citas</h2>
          <p className="texto-suave">
            {esAdministrador
              ? "Consulte todas las citas y registre observaciones administrativas."
              : "Gestione su agenda: confirme, cancele o registre la atención."}
          </p>
        </div>
        {esProfesional ? (
          <button type="button" className="boton" onClick={abrirCrear}>
            Nueva cita
          </button>
        ) : null}
      </div>

      <Alerta tipo="ok" onCerrar={() => setAviso("")}>
        {aviso}
      </Alerta>
      <Alerta onCerrar={() => setError("")}>{error}</Alerta>

      <form className="panel filtros" onSubmit={aplicarFiltros}>
        <Campo etiqueta="Paciente (RUT)" htmlFor="cita-filtro-paciente">
          <input
            id="cita-filtro-paciente"
            type="text"
            value={borrador.paciente_rut}
            placeholder="Búsqueda parcial"
            onChange={(evento) =>
              setBorrador({ ...borrador, paciente_rut: evento.target.value })
            }
          />
        </Campo>
        <Campo etiqueta="Estado" htmlFor="cita-filtro-estado">
          <select
            id="cita-filtro-estado"
            value={borrador.estado}
            onChange={(evento) => setBorrador({ ...borrador, estado: evento.target.value })}
          >
            <option value="">Todos</option>
            {ESTADOS.map((estado) => (
              <option key={estado} value={estado}>
                {etiquetaEstado(estado)}
              </option>
            ))}
          </select>
        </Campo>
        <Campo etiqueta="Desde" htmlFor="cita-filtro-desde">
          <input
            id="cita-filtro-desde"
            type="date"
            value={borrador.desde}
            onChange={(evento) => setBorrador({ ...borrador, desde: evento.target.value })}
          />
        </Campo>
        <Campo etiqueta="Hasta" htmlFor="cita-filtro-hasta">
          <input
            id="cita-filtro-hasta"
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
                    <th>Horario</th>
                    <th>Paciente</th>
                    <th>Profesional</th>
                    <th>Motivo</th>
                    <th>Estado</th>
                    <th aria-label="Acciones" />
                  </tr>
                </thead>
                <tbody>
                  {datos.items.map((cita) => {
                    const esDueno = cita.profesional_rut === usuario?.rut;
                    const puedeGestionar = esProfesional && esDueno;
                    const ocupada = accionando === cita.id_cita;

                    return (
                      <tr key={cita.id_cita}>
                        <td>{formatearRango(cita.fecha_hora_inicio, cita.fecha_hora_fin)}</td>
                        <td className="mono">{cita.paciente_rut}</td>
                        <td className="mono">{cita.profesional_rut}</td>
                        <td>{cita.motivo}</td>
                        <td>
                          <InsigniaEstado estado={cita.estado} />
                        </td>
                        <td className="tabla__acciones">
                          <button
                            type="button"
                            className="boton boton--secundario boton--pequeno"
                            onClick={() => {
                              setErrorModal("");
                              setModal({ tipo: "detalle", cita });
                            }}
                          >
                            Ver
                          </button>

                          {puedeGestionar && cita.estado === "pendiente" ? (
                            <button
                              type="button"
                              className="boton boton--pequeno"
                              disabled={ocupada}
                              onClick={() =>
                                cambiarEstado(cita, "confirmar", "Cita confirmada.")
                              }
                            >
                              Confirmar
                            </button>
                          ) : null}

                          {puedeGestionar && cita.estado === "confirmada" ? (
                            <button
                              type="button"
                              className="boton boton--pequeno"
                              onClick={() => abrirAtencion(cita)}
                            >
                              Registrar atención
                            </button>
                          ) : null}

                          {puedeGestionar && cita.estado === "confirmada" ? (
                            <button
                              type="button"
                              className="boton boton--secundario boton--pequeno"
                              disabled={ocupada}
                              onClick={() =>
                                cambiarEstado(cita, "ausente", "Cita marcada como ausente.")
                              }
                            >
                              Ausente
                            </button>
                          ) : null}

                          {puedeGestionar &&
                          ["pendiente", "confirmada"].includes(cita.estado) ? (
                            <button
                              type="button"
                              className="boton boton--peligro boton--pequeno"
                              disabled={ocupada}
                              onClick={() =>
                                cambiarEstado(cita, "cancelar", "Cita cancelada.")
                              }
                            >
                              Cancelar
                            </button>
                          ) : null}

                          {esAdministrador ? (
                            <button
                              type="button"
                              className="boton boton--secundario boton--pequeno"
                              onClick={() => abrirObservaciones(cita)}
                            >
                              Observaciones
                            </button>
                          ) : null}
                        </td>
                      </tr>
                    );
                  })}
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

      {modal?.tipo === "detalle" ? (
        <Modal titulo="Detalle de la cita" onCerrar={() => setModal(null)}>
          <DetalleLista>
            <DetalleItem etiqueta="Paciente">{modal.cita.paciente_rut}</DetalleItem>
            <DetalleItem etiqueta="Profesional">{modal.cita.profesional_rut}</DetalleItem>
            <DetalleItem etiqueta="Inicio">
              {formatearFechaHora(modal.cita.fecha_hora_inicio)}
            </DetalleItem>
            <DetalleItem etiqueta="Fin">
              {formatearFechaHora(modal.cita.fecha_hora_fin)}
            </DetalleItem>
            <DetalleItem etiqueta="Motivo">{modal.cita.motivo}</DetalleItem>
            <DetalleItem etiqueta="Estado">
              <InsigniaEstado estado={modal.cita.estado} />
            </DetalleItem>
            <DetalleItem etiqueta="Observaciones administrativas">
              {modal.cita.observaciones_administrativas || "Sin observaciones"}
            </DetalleItem>
            <DetalleItem etiqueta="Registrada por">{modal.cita.creado_por_rut}</DetalleItem>
            <DetalleItem etiqueta="Fecha de creación">
              {formatearFechaHora(modal.cita.fecha_creacion)}
            </DetalleItem>
            <DetalleItem etiqueta="Última actualización">
              {formatearFechaHora(modal.cita.fecha_actualizacion)}
            </DetalleItem>
          </DetalleLista>
          <div className="modal__pie">
            <button type="button" className="boton" onClick={() => setModal(null)}>
              Cerrar
            </button>
          </div>
        </Modal>
      ) : null}

      {modal?.tipo === "crear" ? (
        <Modal titulo="Nueva cita" onCerrar={() => setModal(null)}>
          <form className="formulario" onSubmit={crearCita}>
            <Alerta>{errorModal}</Alerta>

            <Campo
              etiqueta="Paciente"
              htmlFor="cita-paciente"
              requerido
              ayuda={
                nuevaCita.paciente_nombre
                  ? `Seleccionado: ${nuevaCita.paciente_nombre}`
                  : "Escriba el RUT y elija una coincidencia."
              }
            >
              <BuscadorRut
                id="cita-paciente"
                valor={nuevaCita.paciente_rut}
                onCambio={(rut, item) =>
                  setNuevaCita({
                    ...nuevaCita,
                    paciente_rut: rut,
                    paciente_nombre: item ? `${item.nombres} ${item.apellidos}` : "",
                  })
                }
              />
            </Campo>

            <div className="formulario__grilla">
              <Campo etiqueta="Inicio" htmlFor="cita-inicio" requerido>
                <input
                  id="cita-inicio"
                  type="datetime-local"
                  value={nuevaCita.inicio}
                  onChange={(evento) =>
                    setNuevaCita({ ...nuevaCita, inicio: evento.target.value })
                  }
                  required
                />
              </Campo>
              <Campo etiqueta="Fin" htmlFor="cita-fin" requerido>
                <input
                  id="cita-fin"
                  type="datetime-local"
                  value={nuevaCita.fin}
                  onChange={(evento) =>
                    setNuevaCita({ ...nuevaCita, fin: evento.target.value })
                  }
                  required
                />
              </Campo>
            </div>

            <Campo etiqueta="Motivo" htmlFor="cita-motivo" requerido>
              <textarea
                id="cita-motivo"
                rows={3}
                maxLength={500}
                value={nuevaCita.motivo}
                onChange={(evento) =>
                  setNuevaCita({ ...nuevaCita, motivo: evento.target.value })
                }
                required
              />
            </Campo>

            <div className="modal__pie">
              <button
                type="button"
                className="boton boton--secundario"
                onClick={() => setModal(null)}
                disabled={guardando}
              >
                Cancelar
              </button>
              <button type="submit" className="boton" disabled={guardando}>
                {guardando ? "Agendando…" : "Agendar cita"}
              </button>
            </div>
          </form>
        </Modal>
      ) : null}

      {modal?.tipo === "atencion" ? (
        <Modal
          titulo="Registrar atención"
          onCerrar={() => setModal(null)}
          ancho="ancho"
        >
          <p className="texto-suave">
            Cita de {formatearRango(modal.cita.fecha_hora_inicio, modal.cita.fecha_hora_fin)} con
            el paciente {modal.cita.paciente_rut}. Al guardar, la cita pasará a estado
            atendida.
          </p>
          <form className="formulario" onSubmit={registrarAtencion}>
            <Alerta>{errorModal}</Alerta>

            <div className="formulario__grilla">
              <Campo
                etiqueta="Fecha y hora de la atención"
                htmlFor="atencion-fecha"
                requerido
                ayuda="Debe estar dentro del horario de la cita."
              >
                <input
                  id="atencion-fecha"
                  type="datetime-local"
                  value={atencion.fecha_atencion}
                  min={aDatetimeLocal(modal.cita.fecha_hora_inicio)}
                  max={aDatetimeLocal(modal.cita.fecha_hora_fin)}
                  onChange={(evento) =>
                    setAtencion({ ...atencion, fecha_atencion: evento.target.value })
                  }
                  required
                />
              </Campo>

              <Campo etiqueta="Motivo" htmlFor="atencion-motivo" requerido>
                <input
                  id="atencion-motivo"
                  type="text"
                  maxLength={500}
                  value={atencion.motivo}
                  onChange={(evento) =>
                    setAtencion({ ...atencion, motivo: evento.target.value })
                  }
                  required
                />
              </Campo>
            </div>

            <Campo
              etiqueta="Registro clínico"
              htmlFor="atencion-registro"
              requerido
              ayuda="Máximo 10.000 caracteres."
            >
              <textarea
                id="atencion-registro"
                rows={8}
                maxLength={10000}
                value={atencion.registro_clinico}
                onChange={(evento) =>
                  setAtencion({ ...atencion, registro_clinico: evento.target.value })
                }
                required
              />
            </Campo>

            <div className="modal__pie">
              <button
                type="button"
                className="boton boton--secundario"
                onClick={() => setModal(null)}
                disabled={guardando}
              >
                Cancelar
              </button>
              <button type="submit" className="boton" disabled={guardando}>
                {guardando ? "Registrando…" : "Registrar atención"}
              </button>
            </div>
          </form>
        </Modal>
      ) : null}

      {modal?.tipo === "observaciones" ? (
        <Modal
          titulo="Observaciones administrativas"
          onCerrar={() => setModal(null)}
          ancho="angosto"
        >
          <form className="formulario" onSubmit={guardarObservaciones}>
            <Alerta>{errorModal}</Alerta>
            <Campo
              etiqueta="Observaciones"
              htmlFor="cita-observaciones"
              ayuda="Máximo 1.000 caracteres. Deje vacío para borrarlas."
            >
              <textarea
                id="cita-observaciones"
                rows={5}
                maxLength={1000}
                value={observaciones}
                onChange={(evento) => setObservaciones(evento.target.value)}
              />
            </Campo>
            <div className="modal__pie">
              <button
                type="button"
                className="boton boton--secundario"
                onClick={() => setModal(null)}
                disabled={guardando}
              >
                Cancelar
              </button>
              <button type="submit" className="boton" disabled={guardando}>
                {guardando ? "Guardando…" : "Guardar"}
              </button>
            </div>
          </form>
        </Modal>
      ) : null}
    </div>
  );
}
