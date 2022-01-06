import datetime
from pydantic import BaseModel
from typing import List

from schemas.album import Album


class EventBase(BaseModel):
    name: str
    timestamp: datetime.datetime


class EventCreate(EventBase):
    pass


class EventList(EventBase):
    id: str


class Event(EventList):
    no_albums: int
    albums: List[Album]

    class Config:
        orm_mode = True
