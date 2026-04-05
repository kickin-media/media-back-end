from sqlmodel import SQLModel, Field
from typing import Optional, List


class TagBase(SQLModel):
    tag_slug: str
    tag_description: str
    supports_value: bool


class Tag(TagBase, table=True):
    __tablename__ = "tags"

    tag_slug: str = Field(primary_key=True)


class TagReadList(TagBase):
    pass


class TagRequest(SQLModel):
    tag: str
    value: Optional[str] = None


class PhotoTagRead(SQLModel):
    tag_slug: str
    tag_value: Optional[str] = None


class SearchRequest(SQLModel):
    tags: List[TagRequest]
