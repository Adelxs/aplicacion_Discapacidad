import { useCallback, useEffect, useState } from "react";

import { pedir } from "../api.js";
import { useAuth } from "../auth.jsx";
import {
  Alerta,
  Campo,
  Cargando,
  Insignia,
  InsigniaRol,
  Modal,
  Paginacion,
  Vacio,
} from "../components/Comunes.jsx";
import { formatearFechaHora } from "../formato.js";

const FORM_VACIO = {
  rut: "",
  nombres: "",
  apellidos: "",
  correo_electronico: "",
  password: "",
  rol: "profesional",
  activo: true,
};

export default function Usuarios() {
  const { usuario: usuarioActual } = useAuth();
  const [borrador, setBorrador] = useState({ rut: "", rol: "", activo: "" });
  const [filtros, setFiltros] = useState({ rut: "", rol: "", activo: "" });
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
      if (filtros.rol) params.set("rol", filtros.rol);
      if (filtros.activo !== "") params.set("activo", filtros.activo);

      const respuesta = await pedir(`/api/v1/usuarios?${params}`);
      setDatos(respuesta);
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

  const abrirEditar = (usuario) => {
    setForm({
      rut: usuario.rut,
      nombres: usuario.nombres,
      apellidos: usuario.apellidos,
      correo_electronico: usuario.correo_electronico,
      password: "",
      rol: usuario.rol,
      activo: usuario.activo,
    });
    setErrorForm("");
    setModal({ modo: "editar", usuario });
  };

  const guardar = async (evento) => {
    evento.preventDefault();
    setGuardando(true);
    setErrorForm("");

    const cuerpo =
      modal.modo === "crear"
        ? {
            rut: form.rut,
            nombres: form.nombres,
            apellidos: form.apellidos,
            correo_electronico: form.correo_electronico,
            password: form.password,
            rol: form.rol,
            activo: form.activo,
          }
        : {
            nombres: form.nombres,
            apellidos: form.apellidos,
            correo_electronico: form.correo_electronico,
            rol: form.rol,
            activo: form.activo,
          };

    try {
      if (modal.modo === "crear") {
        await pedir("/api/v1/usuarios", { metodo: "POST", cuerpo });
        setAviso(`Usuario ${form.rut} creado.`);
      } else {
        await pedir(`/api/v1/usuarios/${encodeURIComponent(modal.usuario.rut)}`, {
          metodo: "PATCH",
          cuerpo,
        });
        setAviso(`Usuario ${modal.usuario.rut} actualizado.`);
      }
      setModal(null);
      setRecarga((valor) => valor + 1);
    } catch (fallo) {
      setErrorForm(fallo.message);
    } finally {
      setGuardando(false);
    }
  };

  const esPropio = modal?.usuario?.rut === usuarioActual?.rut;

  return (
    <div className="pila">
      <div className="pagina__cabecera">
        <div>
          <h2>Cuentas del sistema</h2>
          <p className="texto-suave">
            Solo el administrador puede crear cuentas y cambiar roles o estado.
          </p>
        </div>
        <button type="button" className="boton" onClick={abrirCrear}>
          Nuevo usuario
        </button>
      </div>

      <Alerta tipo="ok" onCerrar={() => setAviso("")}>
        {aviso}
      </Alerta>
      <Alerta onCerrar={() => setError("")}>{error}</Alerta>

      <form className="panel filtros" onSubmit={aplicarFiltros}>
        <Campo etiqueta="RUT" htmlFor="filtro-rut">
          <input
            id="filtro-rut"
            type="text"
            value={borrador.rut}
            placeholder="Búsqueda parcial"
            onChange={(evento) => setBorrador({ ...borrador, rut: evento.target.value })}
          />
        </Campo>
        <Campo etiqueta="Rol" htmlFor="filtro-rol">
          <select
            id="filtro-rol"
            value={borrador.rol}
            onChange={(evento) => setBorrador({ ...borrador, rol: evento.target.value })}
          >
            <option value="">Todos</option>
            <option value="administrador">Administrador</option>
            <option value="profesional">Profesional</option>
          </select>
        </Campo>
        <Campo etiqueta="Estado" htmlFor="filtro-activo">
          <select
            id="filtro-activo"
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
                    <th>Correo</th>
                    <th>Rol</th>
                    <th>Estado</th>
                    <th>Creado</th>
                    <th aria-label="Acciones" />
                  </tr>
                </thead>
                <tbody>
                  {datos.items.map((usuario) => (
                    <tr key={usuario.rut}>
                      <td className="mono">{usuario.rut}</td>
                      <td>
                        {usuario.nombres} {usuario.apellidos}
                      </td>
                      <td>{usuario.correo_electronico}</td>
                      <td>
                        <InsigniaRol rol={usuario.rol} />
                      </td>
                      <td>
                        <Insignia tono={usuario.activo ? "activo" : "inactivo"}>
                          {usuario.activo ? "Activo" : "Inactivo"}
                        </Insignia>
                      </td>
                      <td>{formatearFechaHora(usuario.fecha_creacion)}</td>
                      <td className="tabla__acciones">
                        <button
                          type="button"
                          className="boton boton--secundario boton--pequeno"
                          onClick={() => abrirEditar(usuario)}
                        >
                          Editar
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

      {modal ? (
        <Modal
          titulo={modal.modo === "crear" ? "Nuevo usuario" : `Editar ${modal.usuario.rut}`}
          onCerrar={() => setModal(null)}
        >
          <form className="formulario" onSubmit={guardar}>
            <Alerta>{errorForm}</Alerta>

            <div className="formulario__grilla">
              <Campo etiqueta="RUT" htmlFor="usuario-rut" requerido>
                <input
                  id="usuario-rut"
                  type="text"
                  value={form.rut}
                  onChange={(evento) => setForm({ ...form, rut: evento.target.value })}
                  placeholder="12.345.678-9"
                  disabled={modal.modo === "editar"}
                  required
                />
              </Campo>

              <Campo etiqueta="Rol" htmlFor="usuario-rol" requerido>
                <select
                  id="usuario-rol"
                  value={form.rol}
                  onChange={(evento) => setForm({ ...form, rol: evento.target.value })}
                  disabled={esPropio}
                >
                  <option value="profesional">Profesional</option>
                  <option value="administrador">Administrador</option>
                </select>
              </Campo>

              <Campo etiqueta="Nombres" htmlFor="usuario-nombres" requerido>
                <input
                  id="usuario-nombres"
                  type="text"
                  value={form.nombres}
                  onChange={(evento) => setForm({ ...form, nombres: evento.target.value })}
                  required
                />
              </Campo>

              <Campo etiqueta="Apellidos" htmlFor="usuario-apellidos" requerido>
                <input
                  id="usuario-apellidos"
                  type="text"
                  value={form.apellidos}
                  onChange={(evento) => setForm({ ...form, apellidos: evento.target.value })}
                  required
                />
              </Campo>

              <Campo etiqueta="Correo electrónico" htmlFor="usuario-correo" requerido>
                <input
                  id="usuario-correo"
                  type="email"
                  value={form.correo_electronico}
                  onChange={(evento) =>
                    setForm({ ...form, correo_electronico: evento.target.value })
                  }
                  required
                />
              </Campo>

              {modal.modo === "crear" ? (
                <Campo
                  etiqueta="Contraseña inicial"
                  htmlFor="usuario-password"
                  requerido
                  ayuda="Mínimo 8 caracteres."
                >
                  <input
                    id="usuario-password"
                    type="password"
                    value={form.password}
                    minLength={8}
                    onChange={(evento) => setForm({ ...form, password: evento.target.value })}
                    required
                  />
                </Campo>
              ) : null}
            </div>

            <label className="casilla">
              <input
                type="checkbox"
                checked={form.activo}
                disabled={esPropio}
                onChange={(evento) => setForm({ ...form, activo: evento.target.checked })}
              />
              Cuenta activa
            </label>

            {esPropio ? (
              <p className="campo__ayuda">
                No puede cambiar su propio rol ni desactivar su cuenta desde aquí.
              </p>
            ) : null}

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
