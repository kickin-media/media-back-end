import datetime

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

from sqlmodels.album import Album


class EventBase(SQLModel):
    name: str
    timestamp: datetime.datetime


class Event(EventBase, table=True):
    __tablename__ = "events"

    id: Optional[str] = Field(primary_key=True, index=True)
    albums: List[Album] = Relationship(back_populates="event")


class EventCreate(EventBase):
    pass
