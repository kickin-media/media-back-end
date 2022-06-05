import datetime

from fastapi import APIRouter, Depends, HTTPException
from auth.auth_bearer import JWTBearer

from database import get_db
from sqlmodel import Session
from typing import List

from models.photo import Photo, OriginalPhotoDownload, PhotoUploadResponse, PhotoReadSingle, PhotoReadSingleStub
from models.author import Author
from models.album import Album
from models.event import EventReadSingle

from variables import S3_BUCKET, S3_UPLOAD_EXPIRY, S3_BUCKET_UPLOAD_PATH, S3_BUCKET_ORIGINAL_PATH, S3_BUCKET_PHOTO_PATH, \
    PHOTO_PROCESSING_SQS_QUEUE, API_BASE

import boto3
import uuid
import json

router = APIRouter(
    prefix="/photo",
    tags=["photo"]
)


@router.get("/{photo_id}", response_model=PhotoReadSingle)
async def get_photo(photo_id: str,
                    db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    return photo


@router.get("/{photo_id}/event", response_model=EventReadSingle)
async def get_photo_event(photo_id: str,
                          db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if len(photo.albums) == 0:
        raise HTTPException(status_code=404, detail="photo_not_in_album")

    return photo.albums[0].event


@router.post("/{photo_id}/exif/{photo_exif_secret}")
async def finalize_upload(photo_id: str, photo_exif_secret: str, request_data: dict,
                          db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.exif_update_secret is None:
        raise HTTPException(status_code=403, detail="photo_doesnt_expect_update")

    if photo_exif_secret != photo.exif_update_secret:
        raise HTTPException(status_code=403, detail="invalid_update_key")

    exif_data = request_data['exif_data']

    photo.exif_data = json.dumps(exif_data)
    photo.upload_processed = True
    photo.exif_update_secret = None

    if 'datetime_original' in exif_data.keys():
        photo.timestamp = exif_data['datetime_original']

    db.add(photo)
    db.commit()

    raise HTTPException(status_code=200, detail="done")


@router.get("/{photo_id}/original", response_model=OriginalPhotoDownload)
async def get_original_photo(photo_id: str,
                             auth_data=Depends(JWTBearer()),
                             db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.author.id != auth_data['sub'] and 'photos:download_other' not in auth_data['permissions']:
        raise HTTPException(status_code=403, detail="can_only_download_own_photos")

    download_params = {
        'Bucket': S3_BUCKET,
        'Key': "/".join([S3_BUCKET_ORIGINAL_PATH, "{}_o.jpg".format(photo.id)])
    }
    download_url = boto3.client('s3').generate_presigned_url('get_object',
                                                             Params=download_params,
                                                             ExpiresIn=300)

    return OriginalPhotoDownload(download_url=download_url)


def trigger_photo_process(photo: Photo, exif_update_secret: str, author: Author, source_path: str,
                          delete_upload: bool = False, delay_seconds: int = 60, ttl: int = 30):
    sqs = boto3.client('sqs')

    sqs_message_body = json.dumps({
        'photo_id': photo.id,
        'photo_secret': photo.secret,
        'exif_update_secret': exif_update_secret,
        'author': author.name,
        'delete_upload': delete_upload,
        'data': {
            'TTL': ttl,
            'S3_BUCKET': S3_BUCKET,
            'S3_SOURCE_PATH': source_path,
            'S3_BUCKET_PHOTO_PATH': S3_BUCKET_PHOTO_PATH,
            'S3_BUCKET_ORIGINAL_PATH': S3_BUCKET_ORIGINAL_PATH,
            'API_BASE': API_BASE
        }
    })

    sqs.send_message(
        QueueUrl=PHOTO_PROCESSING_SQS_QUEUE,
        MessageBody=sqs_message_body,
        DelaySeconds=delay_seconds,
    )


@router.post("/{photo_id}/reprocess")
async def reprocess_photo(photo_id: str,
                          auth_data=Depends(JWTBearer()),
                          db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.author.id != auth_data['sub'] and 'photos:manage_other' not in auth_data['permissions']:
        raise HTTPException(status_code=403, detail="can_only_reprocess_own_photos")

    exif_update_secret = str(uuid.uuid4())
    photo.exif_update_secret = exif_update_secret
    db.add(photo)
    db.commit()

    original_path = "/".join([S3_BUCKET_ORIGINAL_PATH, "{}_o.jpg".format(photo.id)])

    trigger_photo_process(photo=photo, author=photo.author, exif_update_secret=exif_update_secret, delete_upload=True,
                          source_path=original_path, delay_seconds=0, ttl=5)

    raise HTTPException(status_code=200, detail="scheduled")


@router.post("/", response_model=List[PhotoUploadResponse])
async def create_upload(num_uploads: int = 1,
                        auth_data=Depends(JWTBearer(required_permissions=['photos:upload'])),
                        db: Session = Depends(get_db)):
    if num_uploads < 1 or num_uploads > 100:
        raise HTTPException(status_code=500, detail="no_uploads_not_allowed")

    author_id = auth_data['sub']
    author = db.get(Author, author_id)
    if author is None:
        raise HTTPException(status_code=500, detail="create_author_data_first")

    response_list = []

    for i in range(num_uploads):
        photo_id = str(uuid.uuid4())
        photo_secret = str(uuid.uuid4())
        exif_update_secret = str(uuid.uuid4())

        photo = Photo(
            id=photo_id,
            secret=photo_secret,
            uploaded_at=datetime.datetime.utcnow(),
            upload_processed=False,
            author_id=author_id,
            exif_update_secret=exif_update_secret
        )

        upload_url = boto3.client('s3').generate_presigned_post(
            S3_BUCKET,
            "/".join([S3_BUCKET_UPLOAD_PATH, photo.secret, "{}.jpg".format(photo.id)]),
            ExpiresIn=S3_UPLOAD_EXPIRY
        )

        db.add(photo)
        db.commit()

        response_list.append(PhotoUploadResponse(
            photo_id=photo.id,
            pre_signed_url=upload_url
        ))

        trigger_photo_process(photo=photo, author=author, exif_update_secret=exif_update_secret, delete_upload=True,
                              source_path=upload_url['fields']['key'])

    return response_list


@router.put("/{photo_id}/albums", response_model=PhotoReadSingleStub)
async def replace_albums(photo_id: str,
                         album_ids: List[str],
                         db: Session = Depends(get_db),
                         auth_data=Depends(JWTBearer())):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.author.id != auth_data['sub'] and 'photos:manage_other' not in auth_data['permissions']:
        raise HTTPException(status_code=403, detail="can_only_manage_own_photos")

    albums = []
    for album_id in album_ids:
        album = db.get(Album, album_id)
        if album is None:
            raise HTTPException(status_code=404, detail="album_not_found_{}".format(album_id))
        albums.append(album)

    for album in photo.albums:
        if album.id not in album_ids:
            if album.cover_id == photo.id:
                album.cover_id = None
                db.add(album)
                db.commit()
                db.refresh(album)

    photo.albums = albums
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return photo


@router.delete("/{photo_id}")
async def delete_photo(photo_id: str,
                       db: Session = Depends(get_db),
                       auth_data=Depends(JWTBearer())):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.author.id != auth_data['sub'] and 'photos:delete_other' not in auth_data['permissions']:
        raise HTTPException(status_code=403, detail="can_only_delete_own_photos")

    for suffix in ['xl', 'l', 'm', 's']:
        s3 = boto3.client('s3')
        s3.delete_object(
            Bucket=S3_BUCKET,
            Key="/".join([S3_BUCKET_PHOTO_PATH, photo.secret, f"{photo.id}_{suffix}.jpg"])
        )
    s3.delete_object(
        Bucket=S3_BUCKET,
        Key="/".join([S3_BUCKET_ORIGINAL_PATH, f"{photo.id}_o.jpg"])
    )

    photo.albums = []
    db.add(photo)
    db.delete(photo)
    db.commit()

    raise HTTPException(status_code=200, detail="photo_deleted")
