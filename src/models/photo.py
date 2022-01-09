import json

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

from models.author import Author
from models.albumphotolink import AlbumPhotoLink

from variables import S3_BUCKET_PHOTO_PATH, S3_PHOTO_HOSTNAME

import datetime


class PhotoBase(SQLModel):
    pass


class Photo(PhotoBase, table=True):
    __tablename__ = "photos"

    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    secret: Optional[str]
    timestamp: Optional[datetime.datetime]
    exif_data: Optional[str]

    uploaded_at: datetime.datetime
    upload_processed: bool

    author_id: str = Field(foreign_key="authors.id")
    author: Author = Relationship(back_populates="photos")

    albums: List["Album"] = Relationship(back_populates="photos", link_model=AlbumPhotoLink)

    @property
    def exif(self):
        filtered_exif = {}
        for k, v in json.loads(self.exif_data).items():
            if 'serial' in k:
                continueq
            filtered_exif[k] = v
        return filtered_exif

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


class PhotoImgUrls(SQLModel):
    original: str
    large: str
    medium: str
    small: str


class PhotoReadList(PhotoBase):
    id: str
    timestamp: Optional[datetime.datetime]
    img_urls: PhotoImgUrls


class PhotoReadSingle(PhotoBase):
    id: str
    timestamp: Optional[datetime.datetime]
    exif: dict
    img_urls: PhotoImgUrls
    author: Author

    # This should be fixed later on, but for now it throws an error I haven't yet been able to solve.
    class Album(SQLModel):
        id: str
        name: str
        timestamp: datetime.datetime

    albums: List[Album]
    # albums: List["AlbumReadList"]


class PhotoUploadPreSignedUrlFields(SQLModel):
    key: str
    AWSAccessKeyId: str
    policy: str
    signature: str


class PhotoUploadPreSignedUrl(SQLModel):
    url: str
    fields: PhotoUploadPreSignedUrlFields


class PhotoUploadResponse(SQLModel):
    photo_id: str
    pre_signed_url: PhotoUploadPreSignedUrl


class OriginalPhotoDownload(SQLModel):
    download_url: str
