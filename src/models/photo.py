import json

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from pydantic import validator

from models.author import Author
from models.albumphotolink import AlbumPhotoLink

from variables import S3_BUCKET_PHOTO_PATH, S3_PHOTO_HOSTNAME

import datetime


class PhotoBase(SQLModel):
    pass


class PhotoImgUrls(SQLModel):
    original: str
    large: str
    medium: str
    small: str


class Photo(PhotoBase, table=True):
    __tablename__ = "photos"

    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    secret: Optional[str]
    timestamp: Optional[datetime.datetime]
    exif_data: Optional[str]
    exif_update_secret: Optional[str]

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
                continue
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
        for size_name, size_suffix in sizes.items():
            url_dict[size_name] = "/".join(
                [S3_PHOTO_HOSTNAME, S3_BUCKET_PHOTO_PATH, self.secret, "{}{}.jpg".format(self.id, size_suffix)])
        return url_dict


class PhotoReadList(PhotoBase):
    id: str
    timestamp: Optional[datetime.datetime]
    img_urls: PhotoImgUrls
    upload_processed: bool
    uploaded_at: datetime.datetime


class PhotoStream(PhotoBase):
    page: int
    photos: List[PhotoReadList]


class PhotoReadSingleStub(PhotoReadList):
    author: Author


class PhotoReadSingle(PhotoReadSingleStub):
    # exif: dict

    # This should be fixed later on, but for now it throws an error I haven't yet been able to solve.
    class Album(SQLModel):
        id: str
        name: str
        timestamp: datetime.datetime
        cover_photo: Optional[PhotoReadSingleStub]

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
