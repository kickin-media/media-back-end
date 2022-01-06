from sqlmodel import SQLModel, Field, String, Relationship, DateTime, Boolean
from typing import Optional, List

from sqlmodels.author import Author
from sqlmodels.albumphotolink import AlbumPhotoLink

from variables import S3_BUCKET_PHOTO_PATH, S3_PHOTO_HOSTNAME


class Photo(SQLModel, table=True):
    id: Optional[String] = Field(default=None, primary_key=True, index=True)
    secret: Optional[String]
    timestamp: DateTime
    exif_data: String

    uploaded_at: DateTime
    upload_processed: Boolean

    author_id: String = Field(foreign_key="authors.id")
    author: Author = Relationship(back_populates="photos")

    albums: List["Album"] = Relationship(back_populates="photos", link_model=AlbumPhotoLink)

    # @property
    # def img_urls(self):
    #     sizes = {
    #         'original': '_xl',
    #         'large': '_l',
    #         'medium': '_m',
    #         'small': '_s'
    #     }
    #     url_dict = {}
    #     for k, v in sizes.items():
    #         url_dict[k] = "/".join(
    #             [S3_PHOTO_HOSTNAME, S3_BUCKET_PHOTO_PATH, self.secret, "{}{}.jpg".format(self.id, v)])
    #     return url_dict
