import datetime

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class AuthorBase(SQLModel):
    name: str


class Author(AuthorBase, table=True):
    __tablename__ = "authors"

    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    photos: List["Photo"] = Relationship(back_populates="author")

    @property
    def photos_count(self):
        return len(self.photos)


class AuthorCreate(AuthorBase):
    pass


class AuthorReadSingle(AuthorBase):
    id: str
    photos_count: int

    # This should be fixed later on, but for now it throws an error I haven't yet been able to solve.
    class Photo(SQLModel):
        id: str
        timestamp: Optional[datetime.datetime]
        img_urls: dict

    photos: List[Photo]
