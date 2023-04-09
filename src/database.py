import sqlalchemy.pool
from sqlmodel import create_engine as create_sqlmodel_engine
from sqlmodel import Session
from sqlmodel.sql.expression import Select, SelectOfScalar

from variables import DB_CONNECTION_STRING

engine = create_sqlmodel_engine(DB_CONNECTION_STRING, poolclass=sqlalchemy.pool.NullPool)

db_session = Session(engine)


def get_db():
    with Session(engine) as session:
        yield session


# From https://github.com/tiangolo/sqlmodel/issues/189#issuecomment-1025190094
SelectOfScalar.inherit_cache = True  # type: ignore
Select.inherit_cache = True  # type: ignore
