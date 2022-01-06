import datetime
from pydantic import BaseModel
from typing import List
from schemas.photo import Photo


class AlbumBase(BaseModel):
    name: str
    timestamp: datetime.datetime
    event_id: str


class AlbumCreate(AlbumBase):
    pass


class Album(AlbumBase):
    id: str
    photos: List[Photo]
    no_photos: int

    class Config:
        orm_mode = True