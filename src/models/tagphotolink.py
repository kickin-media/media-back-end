from sqlmodel import SQLModel, Field


class TagPhotoLink(SQLModel, table=True):
    __tablename__ = "tags_photos"

    tag_slug: str = Field(foreign_key="tags.tag_slug", primary_key=True, index=True)
    photo_id: str = Field(foreign_key="photos.id", primary_key=True, index=True)
    tag_value: str = Field(default="", primary_key=True)
