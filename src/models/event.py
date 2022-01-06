from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from typing import Optional

from database import Base
from models.album import Album


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    timestamp = Column(DateTime)

    albums = relationship(Album, back_populates="event")

    @property
    def no_albums(self):
        return len(self.albums)


class EventList(Event):
    albums = Optional[None]
    no_albums = Optional[None]
