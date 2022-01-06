from sqlmodel import create_engine as create_sqlmodel_engine
from sqlmodel import Session

from variables import DB_CONNECTION_STRING

engine = create_sqlmodel_engine(DB_CONNECTION_STRING)

db_session = Session(engine)


def get_db():
    with Session(engine) as session:
        yield session
