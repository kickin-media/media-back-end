import json

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from pydantic import validator

from models.author import Author
from models.albumphotolink import AlbumPhotoLink

from variables import S3_BUCKET_PHOTO_PATH, S3_PHOTO_HOSTNAME, MAPBOX_API_TOKEN

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

    views: int = Field(default=0)

    gps_lat: float = Field(default=None)
    gps_lon: float = Field(default=None)

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

    @property
    def gps_thumb(self):
        if self.gps_lat is not None and self.gps_lon is not None:
            return "https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/pin-s+ff2600({lon},{lat})/{lon},{lat},{zoom},0/450x300@2x?access_token={token}".format(
                token=MAPBOX_API_TOKEN, lat=self.gps_lat, lon=self.gps_lon, zoom=16)
        else:
            return None


class PhotoReadList(PhotoBase):
    id: str
    timestamp: Optional[datetime.datetime]
    img_urls: PhotoImgUrls
    upload_processed: bool
    uploaded_at: datetime.datetime
    views: int


class PhotoStream(SQLModel):
    photos: List[PhotoReadList]
    next_photo_id: str
    next_timestamp: str


class PhotoReadSingleStub(PhotoReadList):
    author: Author


class PhotoReadSingle(PhotoReadSingleStub):
    exif: dict

    # This should be fixed later on, but for now it throws an error I haven't yet been able to solve.
    class Album(SQLModel):
        id: str
        name: str
        timestamp: datetime.datetime
        cover_photo: Optional[PhotoReadSingleStub]

    albums: List[Album]
    # albums: List["AlbumReadList"]

    gps_thumb: Optional[str]


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
