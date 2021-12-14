from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from database import Base
from models.album import Album


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    timestamp = Column(Integer)

    albums = relationship(Album, back_populates="event")
