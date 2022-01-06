from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from database import Base
from models.photo import Photo


class Author(Base):
    __tablename__ = "authors"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)

    photos = relationship(Photo, back_populates="author")
