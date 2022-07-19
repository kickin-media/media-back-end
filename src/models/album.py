import datetime

from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING, Optional, List

from models.photo import Photo, PhotoReadList, PhotoReadSingle, PhotoReadSingleStub
from models.albumphotolink import AlbumPhotoLink

if TYPE_CHECKING:
    from models.event import Event, EventReadList


class AlbumBase(SQLModel):
    name: str
    timestamp: datetime.datetime
    release_time: Optional[datetime.datetime] = None
    event_id: str = Field(foreign_key="events.id")
    cover_id: str = Field(foreign_key="photos.id", nullable=True, default=None)


class Album(AlbumBase, table=True):
    __tablename__ = "albums"

    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    hidden_secret: Optional[str] = None

    photos: List[Photo] = Relationship(back_populates="albums", link_model=AlbumPhotoLink)

    event: "Event" = Relationship(back_populates="albums")
    cover: Photo = Relationship()


    @property
    def photos_count(self):
        return len(self.photos)

    @property
    def cover_photo(self):
        if len(self.photos) == 0:
            return None
        elif self.cover:
            return self.cover
        return self.photos[0]


class AlbumCreate(AlbumBase):
    pass


class AlbumReadList(AlbumBase):
    id: str
    photos_count: int
    cover_photo: Optional[PhotoReadSingleStub]
    hidden_secret: Optional[str]


class AlbumReadSingleStub(AlbumReadList):
    # This should be fixed later on, but for now it throws an error I haven't yet been able to solve.
    class Event(SQLModel):
        id: str
        name: str
        timestamp: datetime.datetime

    event: Event
    # event: "EventReadList"


class AlbumReadSingle(AlbumReadSingleStub):
    photos: List[PhotoReadSingleStub]
    hidden_secret: Optional[str]


class AlbumSetSecretStatus(SQLModel):
    is_secret: bool
    refresh_secret: bool


class AlbumSetCover(SQLModel):
    photo_id: Optional[str]
