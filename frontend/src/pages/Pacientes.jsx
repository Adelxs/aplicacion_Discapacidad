import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { pedir } from "../api.js";
import { useAuth } from "../auth.jsx";
import {
  Alerta,
  Campo,
  Cargando,
  Confirmar,
  Insignia,
  Modal,
  Paginacion,
  Vacio,
} from "../components/Comunes.jsx";
import { formatearFecha } from "../formato.js";

const FORM_VACIO = {
  rut: "",
  nombres: "",
  apellidos: "",
  fecha_nacimiento: "",
  telefono: "",
  correo_electronico: "",
  direccion: "",
  activo: true,
};

export default function Pacientes() {
  const { esAdministrador } = useAuth();
  const navegar = useNavigate();
  const [borrador, setBorrador] = useState({ rut: "", activo: "" });
  const [filtros, setFiltros] = useState({ rut: "", activo: "" });
  const [pagina, setPagina] = useState(1);
  const [datos, setDatos] = useState({ items: [], total: 0, pages: 1 });
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [recarga, setRecarga] = useState(0);

  const [modal, setModal] = useState(null);
  const [form, setForm] = useState(FORM_VACIO);
  const [errorForm, setErrorForm] = useState("");
  const [guardando, setGuardando] = useState(false);

  const [porEliminar, setPorEliminar] = useState(null);
  const [eliminando, setEliminando] = useState(false);
  const [errorEliminar, setErrorEliminar] = useState("");

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const params = new URLSearchParams({ page: String(pagina), per_page: "20" });
      if (filtros.rut) params.set("rut", filtros.rut);
      if (filtros.activo !== "") params.set("activo", filtros.activo);

      setDatos(await pedir(`/api/v1/pacientes?${params}`));
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

  const abrirCrear = () => {
    setForm(FORM_VACIO);
    setErrorForm("");
    setModal({ modo: "crear" });
  };

  const abrirEditar = (paciente) => {
    setForm({
      rut: paciente.rut,
      nombres: paciente.nombres,
      apellidos: paciente.apellidos,
      fecha_nacimiento: paciente.fecha_nacimiento,
      telefono: paciente.telefono,
      correo_electronico: paciente.correo_electronico,
      direccion: paciente.direccion,
      activo: paciente.activo,
    });
    setErrorForm("");
    setModal({ modo: "editar", paciente });
  };

  const guardar = async (evento) => {
    evento.preventDefault();
    setGuardando(true);
    setErrorForm("");

    const base = {
      nombres: form.nombres,
      apellidos: form.apellidos,
      fecha_nacimiento: form.fecha_nacimiento,
      telefono: form.telefono,
      correo_electronico: form.correo_electronico,
      direccion: form.direccion,
      activo: form.activo,
    };

    try {
      if (modal.modo === "crear") {
        await pedir("/api/v1/pacientes", {
          metodo: "POST",
          cuerpo: { ...base, rut: form.rut },
        });
        setAviso(`Paciente ${form.rut} creado.`);
      } else {
        await pedir(`/api/v1/pacientes/${encodeURIComponent(modal.paciente.rut)}`, {
          metodo: "PATCH",
          cuerpo: base,
        });
        setAviso(`Paciente ${modal.paciente.rut} actualizado.`);
      }
      setModal(null);
      setRecarga((valor) => valor + 1);
    } catch (fallo) {
      setErrorForm(fallo.message);
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async () => {
    setEliminando(true);
    setErrorEliminar("");
    try {
      await pedir(`/api/v1/pacientes/${encodeURIComponent(porEliminar.rut)}`, {
        metodo: "DELETE",
      });
      setAviso(`Paciente ${porEliminar.rut} eliminado.`);
      setPorEliminar(null);
      setRecarga((valor) => valor + 1);
    } catch (fallo) {
      setErrorEliminar(fallo.message);
    } finally {
      setEliminando(false);
    }
  };

  return (
    <div className="pila">
      <div className="pagina__cabecera">
        <div>
          <h2>Fichas de pacientes</h2>
          <p className="texto-suave">
            {esAdministrador
              ? "Cree, actualice o elimine pacientes sin historial clínico."
              : "Consulte los datos de contacto de sus pacientes."}
          </p>
        </div>
        {esAdministrador ? (
          <button type="button" className="boton" onClick={abrirCrear}>
            Nuevo paciente
          </button>
        ) : null}
      </div>

      <Alerta tipo="ok" onCerrar={() => setAviso("")}>
        {aviso}
      </Alerta>
      <Alerta onCerrar={() => setError("")}>{error}</Alerta>

      <form className="panel filtros" onSubmit={aplicarFiltros}>
        <Campo etiqueta="RUT" htmlFor="paciente-filtro-rut">
          <input
            id="paciente-filtro-rut"
            type="text"
            value={borrador.rut}
            placeholder="Búsqueda parcial"
            onChange={(evento) => setBorrador({ ...borrador, rut: evento.target.value })}
          />
        </Campo>
        <Campo etiqueta="Estado" htmlFor="paciente-filtro-activo">
          <select
            id="paciente-filtro-activo"
            value={borrador.activo}
            onChange={(evento) => setBorrador({ ...borrador, activo: evento.target.value })}
          >
            <option value="">Todos</option>
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
          </select>
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
                    <th>RUT</th>
                    <th>Nombre</th>
                    <th>Nacimiento</th>
                    <th>Contacto</th>
                    <th>Dirección</th>
                    <th>Estado</th>
                    <th aria-label="Acciones" />
                  </tr>
                </thead>
                <tbody>
                  {datos.items.map((paciente) => (
                    <tr key={paciente.rut}>
                      <td className="mono">{paciente.rut}</td>
                      <td>
                        {paciente.nombres} {paciente.apellidos}
                      </td>
                      <td>{formatearFecha(paciente.fecha_nacimiento)}</td>
                      <td>
                        <span className="dato-apilado">{paciente.telefono}</span>
                        <span className="dato-apilado texto-suave">
                          {paciente.correo_electronico}
                        </span>
                      </td>
                      <td>{paciente.direccion}</td>
                      <td>
                        <Insignia tono={paciente.activo ? "activo" : "inactivo"}>
                          {paciente.activo ? "Activo" : "Inactivo"}
                        </Insignia>
                      </td>
                      <td className="tabla__acciones">
                        <button
                          type="button"
                          className="boton boton--secundario boton--pequeno"
                          onClick={() =>
                            navegar(`/documentos?paciente=${encodeURIComponent(paciente.rut)}`)
                          }
                        >
                          Documentos
                        </button>
                        {esAdministrador ? (
                          <>
                            <button
                              type="button"
                              className="boton boton--secundario boton--pequeno"
                              onClick={() => abrirEditar(paciente)}
                            >
                              Editar
                            </button>
                            <button
                              type="button"
                              className="boton boton--peligro boton--pequeno"
                              onClick={() => {
                                setErrorEliminar("");
                                setPorEliminar(paciente);
                              }}
                            >
                              Eliminar
                            </button>
                          </>
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

      {modal ? (
        <Modal
          titulo={
            modal.modo === "crear" ? "Nuevo paciente" : `Editar ${modal.paciente.rut}`
          }
          onCerrar={() => setModal(null)}
          ancho="ancho"
        >
          <form className="formulario" onSubmit={guardar}>
            <Alerta>{errorForm}</Alerta>

            <div className="formulario__grilla">
              <Campo etiqueta="RUT" htmlFor="paciente-rut" requerido>
                <input
                  id="paciente-rut"
                  type="text"
                  value={form.rut}
                  onChange={(evento) => setForm({ ...form, rut: evento.target.value })}
                  placeholder="12.345.678-9"
                  disabled={modal.modo === "editar"}
                  required
                />
              </Campo>

              <Campo etiqueta="Fecha de nacimiento" htmlFor="paciente-nacimiento" requerido>
                <input
                  id="paciente-nacimiento"
                  type="date"
                  value={form.fecha_nacimiento}
                  max={new Date().toISOString().slice(0, 10)}
                  onChange={(evento) =>
                    setForm({ ...form, fecha_nacimiento: evento.target.value })
                  }
                  required
                />
              </Campo>

              <Campo etiqueta="Nombres" htmlFor="paciente-nombres" requerido>
                <input
                  id="paciente-nombres"
                  type="text"
                  value={form.nombres}
                  onChange={(evento) => setForm({ ...form, nombres: evento.target.value })}
                  required
                />
              </Campo>

              <Campo etiqueta="Apellidos" htmlFor="paciente-apellidos" requerido>
                <input
                  id="paciente-apellidos"
                  type="text"
                  value={form.apellidos}
                  onChange={(evento) => setForm({ ...form, apellidos: evento.target.value })}
                  required
                />
              </Campo>

              <Campo etiqueta="Teléfono" htmlFor="paciente-telefono" requerido>
                <input
                  id="paciente-telefono"
                  type="text"
                  value={form.telefono}
                  onChange={(evento) => setForm({ ...form, telefono: evento.target.value })}
                  placeholder="+56912345678"
                  required
                />
              </Campo>

              <Campo etiqueta="Correo electrónico" htmlFor="paciente-correo" requerido>
                <input
                  id="paciente-correo"
                  type="email"
                  value={form.correo_electronico}
                  onChange={(evento) =>
                    setForm({ ...form, correo_electronico: evento.target.value })
                  }
                  required
                />
              </Campo>

              <Campo etiqueta="Dirección" htmlFor="paciente-direccion" requerido>
                <input
                  id="paciente-direccion"
                  type="text"
                  value={form.direccion}
                  onChange={(evento) => setForm({ ...form, direccion: evento.target.value })}
                  required
                />
              </Campo>
            </div>

            <label className="casilla">
              <input
                type="checkbox"
                checked={form.activo}
                onChange={(evento) => setForm({ ...form, activo: evento.target.checked })}
              />
              Paciente activo
            </label>

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

      {porEliminar ? (
        <Modal
          titulo="Eliminar paciente"
          onCerrar={() => setPorEliminar(null)}
          ancho="angosto"
        >
          <p>
            ¿Eliminar la ficha de <strong>{porEliminar.nombres} {porEliminar.apellidos}</strong>{" "}
            ({porEliminar.rut})? Esta acción no se puede deshacer.
          </p>
          <Alerta>{errorEliminar}</Alerta>
          <div className="modal__pie">
            <button
              type="button"
              className="boton boton--secundario"
              onClick={() => setPorEliminar(null)}
              disabled={eliminando}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="boton boton--peligro"
              onClick={eliminar}
              disabled={eliminando}
            >
              {eliminando ? "Eliminando…" : "Eliminar"}
            </button>
          </div>
        </Modal>
      ) : null}
    </div>
  );
}
