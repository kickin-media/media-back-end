from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship

from database import Base
from models.associations import albums_photo_association_table


class Album(Base):
    __tablename__ = "albums"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    timestamp = Column(DateTime)
    event_id = Column(String, ForeignKey("events.id"))

    event = relationship("Event", back_populates="albums")
    photos = relationship("Photo", secondary=albums_photo_association_table, backref="albums")

    @property
    def no_photos(self):
        return len(self.photos)


class AlbumList(Album):
    photos = []
