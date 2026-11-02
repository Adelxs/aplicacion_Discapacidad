import { useCallback, useEffect, useState } from "react";

import { pedir } from "../api.js";
import { useAuth } from "../auth.jsx";
import {
  Alerta,
  Campo,
  Cargando,
  Insignia,
  Modal,
  Paginacion,
  Vacio,
} from "../components/Comunes.jsx";

const FORM_VACIO = {
  rut: "",
  nombres: "",
  apellidos: "",
  especialidad: "",
  telefono: "",
  correo_electronico: "",
  usuario_rut: "",
  activo: true,
};

export default function Profesionales() {
  const { esAdministrador } = useAuth();
  const [borrador, setBorrador] = useState({ rut: "", especialidad: "", activo: "" });
  const [filtros, setFiltros] = useState({ rut: "", especialidad: "", activo: "" });
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

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const params = new URLSearchParams({ page: String(pagina), per_page: "20" });
      if (filtros.rut) params.set("rut", filtros.rut);
      if (filtros.especialidad) params.set("especialidad", filtros.especialidad);
      if (filtros.activo !== "") params.set("activo", filtros.activo);

      setDatos(await pedir(`/api/v1/profesionales?${params}`));
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

  const abrirEditar = (profesional) => {
    setForm({
      rut: profesional.rut,
      nombres: profesional.nombres,
      apellidos: profesional.apellidos,
      especialidad: profesional.especialidad,
      telefono: profesional.telefono,
      correo_electronico: profesional.correo_electronico,
      usuario_rut: profesional.usuario_rut ?? "",
      activo: profesional.activo,
    });
    setErrorForm("");
    setModal({ modo: "editar", profesional });
  };

  const guardar = async (evento) => {
    evento.preventDefault();
    setGuardando(true);
    setErrorForm("");

    const base = {
      nombres: form.nombres,
      apellidos: form.apellidos,
      especialidad: form.especialidad,
      telefono: form.telefono,
      correo_electronico: form.correo_electronico,
      activo: form.activo,
    };

    try {
      if (modal.modo === "crear") {
        await pedir("/api/v1/profesionales", {
          metodo: "POST",
          cuerpo: {
            ...base,
            rut: form.rut,
            usuario_rut: form.usuario_rut.trim() || null,
          },
        });
        setAviso(`Profesional ${form.rut} creado.`);
      } else {
        await pedir(
          `/api/v1/profesionales/${encodeURIComponent(modal.profesional.rut)}`,
          { metodo: "PATCH", cuerpo: base },
        );
        setAviso(`Profesional ${modal.profesional.rut} actualizado.`);
      }
      setModal(null);
      setRecarga((valor) => valor + 1);
    } catch (fallo) {
      setErrorForm(fallo.message);
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="pila">
      <div className="pagina__cabecera">
        <div>
          <h2>Profesionales de la salud</h2>
          <p className="texto-suave">
            {esAdministrador
              ? "Gestione los perfiles profesionales y su vínculo con una cuenta de acceso."
              : "Consulte los profesionales registrados y sus especialidades."}
          </p>
        </div>
        {esAdministrador ? (
          <button type="button" className="boton" onClick={abrirCrear}>
            Nuevo profesional
          </button>
        ) : null}
      </div>

      <Alerta tipo="ok" onCerrar={() => setAviso("")}>
        {aviso}
      </Alerta>
      <Alerta onCerrar={() => setError("")}>{error}</Alerta>

      <form className="panel filtros" onSubmit={aplicarFiltros}>
        <Campo etiqueta="RUT" htmlFor="profesional-filtro-rut">
          <input
            id="profesional-filtro-rut"
            type="text"
            value={borrador.rut}
            placeholder="Búsqueda parcial"
            onChange={(evento) => setBorrador({ ...borrador, rut: evento.target.value })}
          />
        </Campo>
        <Campo etiqueta="Especialidad" htmlFor="profesional-filtro-especialidad">
          <input
            id="profesional-filtro-especialidad"
            type="text"
            value={borrador.especialidad}
            onChange={(evento) =>
              setBorrador({ ...borrador, especialidad: evento.target.value })
            }
          />
        </Campo>
        <Campo etiqueta="Estado" htmlFor="profesional-filtro-activo">
          <select
            id="profesional-filtro-activo"
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
                    <th>Especialidad</th>
                    <th>Contacto</th>
                    <th>Cuenta</th>
                    <th>Estado</th>
                    {esAdministrador ? <th aria-label="Acciones" /> : null}
                  </tr>
                </thead>
                <tbody>
                  {datos.items.map((profesional) => (
                    <tr key={profesional.rut}>
                      <td className="mono">{profesional.rut}</td>
                      <td>
                        {profesional.nombres} {profesional.apellidos}
                      </td>
                      <td>{profesional.especialidad}</td>
                      <td>
                        <span className="dato-apilado">{profesional.telefono}</span>
                        <span className="dato-apilado texto-suave">
                          {profesional.correo_electronico}
                        </span>
                      </td>
                      <td className="mono">{profesional.usuario_rut ?? "Sin vincular"}</td>
                      <td>
                        <Insignia tono={profesional.activo ? "activo" : "inactivo"}>
                          {profesional.activo ? "Activo" : "Inactivo"}
                        </Insignia>
                      </td>
                      {esAdministrador ? (
                        <td className="tabla__acciones">
                          <button
                            type="button"
                            className="boton boton--secundario boton--pequeno"
                            onClick={() => abrirEditar(profesional)}
                          >
                            Editar
                          </button>
                        </td>
                      ) : null}
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
            modal.modo === "crear"
              ? "Nuevo profesional"
              : `Editar ${modal.profesional.rut}`
          }
          onCerrar={() => setModal(null)}
        >
          <form className="formulario" onSubmit={guardar}>
            <Alerta>{errorForm}</Alerta>

            <div className="formulario__grilla">
              <Campo etiqueta="RUT" htmlFor="profesional-rut" requerido>
                <input
                  id="profesional-rut"
                  type="text"
                  value={form.rut}
                  onChange={(evento) => setForm({ ...form, rut: evento.target.value })}
                  placeholder="12.345.678-9"
                  disabled={modal.modo === "editar"}
                  required
                />
              </Campo>

              <Campo etiqueta="Especialidad" htmlFor="profesional-especialidad" requerido>
                <input
                  id="profesional-especialidad"
                  type="text"
                  value={form.especialidad}
                  onChange={(evento) =>
                    setForm({ ...form, especialidad: evento.target.value })
                  }
                  required
                />
              </Campo>

              <Campo etiqueta="Nombres" htmlFor="profesional-nombres" requerido>
                <input
                  id="profesional-nombres"
                  type="text"
                  value={form.nombres}
                  onChange={(evento) => setForm({ ...form, nombres: evento.target.value })}
                  required
                />
              </Campo>

              <Campo etiqueta="Apellidos" htmlFor="profesional-apellidos" requerido>
                <input
                  id="profesional-apellidos"
                  type="text"
                  value={form.apellidos}
                  onChange={(evento) => setForm({ ...form, apellidos: evento.target.value })}
                  required
                />
              </Campo>

              <Campo etiqueta="Teléfono" htmlFor="profesional-telefono" requerido>
                <input
                  id="profesional-telefono"
                  type="text"
                  value={form.telefono}
                  onChange={(evento) => setForm({ ...form, telefono: evento.target.value })}
                  required
                />
              </Campo>

              <Campo etiqueta="Correo electrónico" htmlFor="profesional-correo" requerido>
                <input
                  id="profesional-correo"
                  type="email"
                  value={form.correo_electronico}
                  onChange={(evento) =>
                    setForm({ ...form, correo_electronico: evento.target.value })
                  }
                  required
                />
              </Campo>

              <Campo
                etiqueta="Cuenta vinculada (RUT)"
                htmlFor="profesional-usuario"
                ayuda={
                  modal.modo === "crear"
                    ? "Opcional. Debe existir una cuenta con rol profesional y el mismo RUT."
                    : "La vinculación se define al crear el perfil; no se modifica aquí."
                }
              >
                <input
                  id="profesional-usuario"
                  type="text"
                  value={form.usuario_rut}
                  onChange={(evento) =>
                    setForm({ ...form, usuario_rut: evento.target.value })
                  }
                  placeholder={form.rut || "12.345.678-9"}
                  disabled={modal.modo === "editar"}
                />
              </Campo>
            </div>

            <label className="casilla">
              <input
                type="checkbox"
                checked={form.activo}
                onChange={(evento) => setForm({ ...form, activo: evento.target.checked })}
              />
              Perfil activo
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
    </div>
  );
}
