from sqlalchemy import Column, DateTime, String, ForeignKey, Boolean, sql
from sqlalchemy.orm import relationship

from database import Base
from variables import S3_BUCKET_PHOTO_PATH, S3_PHOTO_HOSTNAME


class Photo(Base):
    __tablename__ = "photos"

    id = Column(String, primary_key=True, index=True)
    secret = Column(String)
    timestamp = Column(DateTime)
    author_id = Column(String, ForeignKey("authors.id"))
    exif_data = Column(String)
    uploaded_at = Column(DateTime, server_default=sql.func.now())
    upload_processed = Column(Boolean, server_default=sql.false())

    author = relationship("Author", back_populates="photos")

    @property
    def img_urls(self):
        sizes = {
            'original': '_xl',
            'large': '_l',
            'medium': '_m',
            'small': '_s'
        }
        url_dict = {}
        for k, v in sizes.items():
            url_dict[k] = "/".join(
                [S3_PHOTO_HOSTNAME, S3_BUCKET_PHOTO_PATH, self.secret, "{}{}.jpg".format(self.id, v)])
        return url_dict
