from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from sqlmodel import create_engine as create_sqlmodel_engine
from sqlmodel import Session

from variables import DB_CONNECTION_STRING

# SQL Alchemy
engine = create_engine(DB_CONNECTION_STRING)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLModel
sqlmodel_engine = create_sqlmodel_engine(DB_CONNECTION_STRING)
sqlmodel_session = Session(sqlmodel_engine)


