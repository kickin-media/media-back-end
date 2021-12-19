from sqlalchemy import Column, DateTime, String

from database import Base


class Batch(Base):
    __tablename__ = "uploads"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime)
    expires = Column(DateTime)
    presigned_url = Column(String)
