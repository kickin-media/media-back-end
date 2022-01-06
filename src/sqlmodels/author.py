from sqlmodel import SQLModel, Field, String, Relationship
from typing import Optional, List

from sqlmodels.photo import Photo


class Author(SQLModel, table=True):
    id: Optional[String] = Field(default=None, primary_key=True, index=True)
    name: String

    photos: List[Photo] = Relationship(back_populates="author")
