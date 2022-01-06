from sqlmodel import SQLModel, Field, String, Relationship, DateTime, Boolean
from typing import Optional, List

from sqlmodels.photo import Photo
from sqlmodels.album import Album


class AlbumPhotoLink(SQLModel, table=True):
    album_id: Optional[String] = Field(default=None, foreign_key="albums.id", primary_key=True, index=True)
    photo_id: Optional[String] = Field(default=None, foreign_key="photos.id", primary_key=True, index=True)
