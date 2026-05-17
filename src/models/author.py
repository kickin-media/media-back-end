from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class AuthorBase(SQLModel):
    name: str


class Author(AuthorBase, table=True):
    __tablename__ = "authors"

    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    photos: List["Photo"] = Relationship(back_populates="author")


class AuthorCreate(AuthorBase):
    pass


class AuthorReadSingle(AuthorBase):
    id: str
    photos_count: int