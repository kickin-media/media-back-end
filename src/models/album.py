from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Album(Base):
    __tablename__ = "albums"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    timestamp = Column(Integer)
    event_id = Column(String, ForeignKey("events.id"))

    event = relationship("Event", back_populates="albums")
