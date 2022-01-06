from sqlmodel import SQLModel, Field
from typing import Optional


class AlbumPhotoLink(SQLModel, table=True):
    __tablename__ = "albums_photos"

    album_id: str = Field(foreign_key="albums.id", primary_key=True, index=True)
    photo_id: str = Field(foreign_key="photos.id", primary_key=True, index=True)
