"""Utilidades de paginacion de consultas."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session


def paginar(db: Session, consulta, pagina: int, por_pagina: int) -> dict:
    """Devuelve el cuerpo paginado que esperan los esquemas `Pagina`."""
    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    items = db.scalars(
        consulta.offset((pagina - 1) * por_pagina).limit(por_pagina)
    ).all()

    return {
        "items": items,
        "total": total,
        "page": pagina,
        "per_page": por_pagina,
        "pages": (total + por_pagina - 1) // por_pagina,
    }
