import datetime
from pydantic import BaseModel
from typing import Optional

from schemas.author import Author


class PhotoBase(BaseModel):
    pass


class PhotoCreate(PhotoBase):
    author_id: str


class Photo(PhotoBase):
    id: str
    secret: str
    timestamp: Optional[datetime.datetime]
    author_id: str
    exif_data: Optional[str]
    uploaded_at: datetime.datetime
    upload_processed: bool

    author: Optional[Author]
    img_urls: dict

    class Config:
        orm_mode = True


class PreSignedUrlFields(BaseModel):
    key: str
    AWSAccessKeyId: str
    policy: str
    signature: str


class PreSignedUrlData(BaseModel):
    url: str
    fields: PreSignedUrlFields


class PhotoUpload(Photo):
    pre_signed_url: PreSignedUrlData


class OriginalPhotoDownload(BaseModel):
    download_url: str
