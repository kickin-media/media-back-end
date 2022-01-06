import datetime

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


# from sqlmodels.photo import Photo
# from sqlmodels.albumphotolink import AlbumPhotoLink


class Album(SQLModel, table=True):
    __tablename__ = "albums"

    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    name: str
    timestamp: datetime.datetime

    event_id: str = Field(foreign_key="events.id")
    event: Optional["Event"] = Relationship(back_populates="albums")

    # photos: List[Photo] = Relationship(back_populates="albums", link_model=AlbumPhotoLink)
