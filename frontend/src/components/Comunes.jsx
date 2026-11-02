import { useEffect } from "react";

import { etiquetaEstado, etiquetaRol } from "../formato.js";

export function Alerta({ tipo = "error", children, onCerrar }) {
  if (!children) return null;
  return (
    <div
      className={`alerta alerta--${tipo}`}
      role={tipo === "error" ? "alert" : "status"}
    >
      <span>{children}</span>
      {onCerrar ? (
        <button
          type="button"
          className="alerta__cerrar"
          onClick={onCerrar}
          aria-label="Cerrar aviso"
        >
          ×
        </button>
      ) : null}
    </div>
  );
}

export function Cargando({ texto = "Cargando…" }) {
  return <p className="cargando">{texto}</p>;
}

export function Vacio({ children = "No hay registros para mostrar." }) {
  return <p className="vacio">{children}</p>;
}

export function Campo({ etiqueta, htmlFor, requerido = false, ayuda, children }) {
  return (
    <div className="campo">
      <label htmlFor={htmlFor}>
        {etiqueta}
        {requerido ? <span aria-hidden="true"> *</span> : null}
      </label>
      {children}
      {ayuda ? <p className="campo__ayuda">{ayuda}</p> : null}
    </div>
  );
}

export function Insignia({ tono = "neutro", children }) {
  return <span className={`insignia insignia--${tono}`}>{children}</span>;
}

export function InsigniaEstado({ estado }) {
  return <Insignia tono={estado}>{etiquetaEstado(estado)}</Insignia>;
}

export function InsigniaRol({ rol }) {
  return <Insignia tono={rol}>{etiquetaRol(rol)}</Insignia>;
}

export function Paginacion({ pagina, paginas, total, onCambiar }) {
  if (!paginas || paginas <= 1) {
    return <p className="paginacion__resumen">{total} registro(s)</p>;
  }

  return (
    <div className="paginacion">
      <button
        type="button"
        className="boton boton--secundario boton--pequeno"
        disabled={pagina <= 1}
        onClick={() => onCambiar(pagina - 1)}
      >
        Anterior
      </button>
      <span className="paginacion__resumen">
        Página {pagina} de {paginas} · {total} registro(s)
      </span>
      <button
        type="button"
        className="boton boton--secundario boton--pequeno"
        disabled={pagina >= paginas}
        onClick={() => onCambiar(pagina + 1)}
      >
        Siguiente
      </button>
    </div>
  );
}

export function Modal({ titulo, children, onCerrar, ancho = "normal" }) {
  useEffect(() => {
    const alPresionar = (evento) => {
      if (evento.key === "Escape") onCerrar();
    };
    document.addEventListener("keydown", alPresionar);
    return () => document.removeEventListener("keydown", alPresionar);
  }, [onCerrar]);

  return (
    <div
      className="modal-fondo"
      role="presentation"
      onMouseDown={(evento) => {
        if (evento.target === evento.currentTarget) onCerrar();
      }}
    >
      <div
        className={`modal modal--${ancho}`}
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
      >
        <div className="modal__cabecera">
          <h2>{titulo}</h2>
          <button
            type="button"
            className="modal__cerrar"
            onClick={onCerrar}
            aria-label="Cerrar"
          >
            ×
          </button>
        </div>
        <div className="modal__cuerpo">{children}</div>
      </div>
    </div>
  );
}

export function Confirmar({
  titulo = "Confirmar acción",
  mensaje,
  textoConfirmar = "Confirmar",
  onConfirmar,
  onCancelar,
  cargando = false,
}) {
  return (
    <Modal titulo={titulo} onCerrar={onCancelar} ancho="angosto">
      <p className="confirmar__texto">{mensaje}</p>
      <div className="modal__pie">
        <button
          type="button"
          className="boton boton--secundario"
          onClick={onCancelar}
          disabled={cargando}
        >
          Cancelar
        </button>
        <button
          type="button"
          className="boton boton--peligro"
          onClick={onConfirmar}
          disabled={cargando}
        >
          {cargando ? "Procesando…" : textoConfirmar}
        </button>
      </div>
    </Modal>
  );
}

export function DetalleLista({ children }) {
  return <dl className="detalle-lista">{children}</dl>;
}

export function DetalleItem({ etiqueta, children }) {
  return (
    <div className="detalle-lista__fila">
      <dt>{etiqueta}</dt>
      <dd>{children ?? "—"}</dd>
    </div>
  );
}
