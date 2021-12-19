import datetime
from pydantic import BaseModel


class AlbumBase(BaseModel):
    name: str
    timestamp: datetime.datetime
    event_id: str


class AlbumCreate(AlbumBase):
    pass


class Album(AlbumBase):
    id: str

    class Config:
        orm_mode = True
