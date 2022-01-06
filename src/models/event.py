import datetime

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

from models.album import Album, AlbumReadList


class EventBase(SQLModel):
    name: str
    timestamp: datetime.datetime


class Event(EventBase, table=True):
    __tablename__ = "events"

    id: Optional[str] = Field(primary_key=True, index=True)

    albums: List[Album] = Relationship(back_populates="event")

    @property
    def albums_count(self):
        return len(self.albums)


class EventCreate(EventBase):
    pass


class EventReadList(EventBase):
    id: str
    albums_count: int


class EventReadSingle(EventBase):
    id: str
    albums: List[AlbumReadList]
    albums_count: int
