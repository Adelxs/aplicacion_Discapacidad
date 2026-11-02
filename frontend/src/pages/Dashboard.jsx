import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { pedir } from "../api.js";
import { useAuth } from "../auth.jsx";
import { Alerta, Cargando } from "../components/Comunes.jsx";
import { etiquetaEstado } from "../formato.js";

const ESTADOS = ["pendiente", "confirmada", "atendida", "cancelada", "ausente"];

function TarjetaResumen({ titulo, valor, descripcion, enlace, children }) {
  return (
    <section className="tarjeta-resumen">
      <div className="tarjeta-resumen__cabecera">
        <h2>{titulo}</h2>
        {enlace ? <Link to={enlace}>Ver detalle</Link> : null}
      </div>
      <p className="tarjeta-resumen__valor">{valor}</p>
      {descripcion ? <p className="tarjeta-resumen__descripcion">{descripcion}</p> : null}
      {children}
    </section>
  );
}

export default function Dashboard() {
  const { usuario, esAdministrador } = useAuth();
  const [resumen, setResumen] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    let cancelado = false;

    const cargar = async () => {
      try {
        const consultas = [
          pedir("/api/v1/citas?per_page=1"),
          ...ESTADOS.map((estado) =>
            pedir(`/api/v1/citas?estado=${estado}&per_page=1`),
          ),
          pedir("/api/v1/atenciones?per_page=1"),
          pedir("/api/v1/pacientes?per_page=1"),
          pedir("/api/v1/profesionales?per_page=1"),
          pedir("/api/v1/documentos?per_page=1"),
        ];
        if (esAdministrador) {
          consultas.push(pedir("/api/v1/usuarios?per_page=1"));
        }

        const [citas, ...resto] = await Promise.all(consultas);
        const porEstado = Object.fromEntries(
          ESTADOS.map((estado, indice) => [estado, resto[indice].total]),
        );
        const indiceBase = ESTADOS.length;

        if (!cancelado) {
          setResumen({
            citas: citas.total,
            porEstado,
            atenciones: resto[indiceBase].total,
            pacientes: resto[indiceBase + 1].total,
            profesionales: resto[indiceBase + 2].total,
            documentos: resto[indiceBase + 3].total,
            usuarios: esAdministrador ? resto[indiceBase + 4].total : null,
          });
          setError("");
        }
      } catch (fallo) {
        if (!cancelado) setError(fallo.message);
      } finally {
        if (!cancelado) setCargando(false);
      }
    };

    cargar();
    return () => {
      cancelado = true;
    };
  }, [esAdministrador]);

  const hoy = new Intl.DateTimeFormat("es-CL", {
    dateStyle: "full",
    timeZone: "America/Santiago",
  }).format(new Date());

  return (
    <div className="pila">
      <section className="bienvenida">
        <div>
          <p className="pagina__etiqueta">{hoy}</p>
          <h2>
            Hola, {usuario?.nombres}. {esAdministrador ? "Este es el estado del sistema." : "Esta es tu actividad."}
          </h2>
          <p className="texto-suave">
            {esAdministrador
              ? "Como administrador puedes consultar toda la agenda, las atenciones y los documentos, y gestionar usuarios y pacientes."
              : "Consulta tu agenda, registra atenciones y adjunta documentos de tus pacientes."}
          </p>
        </div>
      </section>

      <Alerta>{error}</Alerta>

      {cargando ? (
        <Cargando texto="Calculando indicadores…" />
      ) : resumen ? (
        <>
          <div className="tarjetas">
            <TarjetaResumen
              titulo="Citas"
              valor={resumen.citas}
              descripcion={esAdministrador ? "Agenda completa del sistema" : "Tu agenda"}
              enlace="/citas"
            >
              <ul className="desglose">
                {ESTADOS.map((estado) => (
                  <li key={estado} className={`desglose__item desglose__item--${estado}`}>
                    <span>{etiquetaEstado(estado)}</span>
                    <strong>{resumen.porEstado[estado]}</strong>
                  </li>
                ))}
              </ul>
            </TarjetaResumen>

            <TarjetaResumen
              titulo="Atenciones"
              valor={resumen.atenciones}
              descripcion={
                esAdministrador ? "Registros clínicos del sistema" : "Tus registros clínicos"
              }
              enlace="/atenciones"
            />

            <TarjetaResumen
              titulo="Pacientes"
              valor={resumen.pacientes}
              descripcion="Fichas de pacientes registradas"
              enlace="/pacientes"
            />

            <TarjetaResumen
              titulo="Documentos"
              valor={resumen.documentos}
              descripcion={
                esAdministrador
                  ? "Archivos privados almacenados"
                  : "Documentos que puedes consultar"
              }
              enlace="/documentos"
            />

            <TarjetaResumen
              titulo="Profesionales"
              valor={resumen.profesionales}
              descripcion="Profesionales con perfil registrado"
              enlace="/profesionales"
            />

            {esAdministrador ? (
              <TarjetaResumen
                titulo="Usuarios"
                valor={resumen.usuarios}
                descripcion="Cuentas habilitadas para ingresar"
                enlace="/usuarios"
              />
            ) : null}
          </div>

          <section className="panel">
            <div className="panel__cabecera">
              <h2>Accesos rápidos</h2>
            </div>
            <div className="accesos">
              <Link className="acceso" to="/citas">
                <strong>Agenda</strong>
                <span>Revisar y gestionar citas</span>
              </Link>
              <Link className="acceso" to="/atenciones">
                <strong>Atenciones</strong>
                <span>Consultar registros clínicos</span>
              </Link>
              <Link className="acceso" to="/documentos">
                <strong>Documentos</strong>
                <span>Subir y descargar archivos</span>
              </Link>
              {esAdministrador ? (
                <Link className="acceso" to="/pacientes">
                  <strong>Pacientes</strong>
                  <span>Crear y actualizar fichas</span>
                </Link>
              ) : (
                <Link className="acceso" to="/pacientes">
                  <strong>Pacientes</strong>
                  <span>Consultar fichas</span>
                </Link>
              )}
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}
