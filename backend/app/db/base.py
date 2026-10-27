"""Base declarativa de SQLAlchemy.

La convencion de nombres es estable desde el inicio para que Alembic pueda
generar migraciones reproducibles en las siguientes etapas.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

CONVENCION_NOMBRES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION_NOMBRES)
