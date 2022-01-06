import datetime

from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING, Optional, List

from models.photo import Photo, PhotoReadList
from models.albumphotolink import AlbumPhotoLink

if TYPE_CHECKING:
    from models.event import Event, EventReadList


class AlbumBase(SQLModel):
    name: str
    timestamp: datetime.datetime
    release_time: Optional[datetime.datetime] = None
    event_id: str = Field(foreign_key="events.id")


class Album(AlbumBase, table=True):
    __tablename__ = "albums"

    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    hidden_secret: Optional[str] = None

    event: "Event" = Relationship(back_populates="albums")

    photos: List[Photo] = Relationship(back_populates="albums", link_model=AlbumPhotoLink)

    @property
    def photos_count(self):
        return len(self.photos)


class AlbumCreate(AlbumBase):
    pass


class AlbumUpdate(AlbumBase):
    event_id: Optional[str] = None


class AlbumReadList(AlbumBase):
    id: str
    photos_count: int


class AlbumReadSingle(AlbumBase):
    id: str
    photos: List[PhotoReadList]
    photos_count: int

    # This should be fixed later on, but for now it throws an error I haven't yet been able to solve.
    class Event(SQLModel):
        id: str
        name: str
        timestamp: datetime.datetime

    event: Event
    # event: "EventReadList"


class AlbumSetSecretStatus(SQLModel):
    is_secret: bool
    refresh_secret: bool
