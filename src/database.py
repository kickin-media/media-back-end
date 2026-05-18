from sqlalchemy.pool import NullPool
from sqlmodel import create_engine as create_sqlmodel_engine
from sqlmodel import Session
from sqlmodel.sql.expression import Select, SelectOfScalar

from variables import DB_CONNECTION_STRING

engine = create_sqlmodel_engine(
    DB_CONNECTION_STRING,
    poolclass=NullPool,
)

def get_db():
    with Session(engine) as session:
        yield session


# From https://github.com/tiangolo/sqlmodel/issues/189#issuecomment-1025190094
SelectOfScalar.inherit_cache = True  # type: ignore
Select.inherit_cache = True  # type: ignore
