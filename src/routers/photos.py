from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import crud.photo
from auth.auth_bearer import JWTBearer
from dependencies import get_db
from schemas.photo import PhotoCreate, PhotoUpload, Photo, OriginalPhotoDownload

from crud.photo import create_photo, update_photo_albums
from crud.author import get_author
from crud.album import get_album
from variables import S3_BUCKET, S3_UPLOAD_EXPIRY, S3_BUCKET_UPLOAD_PATH, S3_BUCKET_ORIGINAL_PATH

from tasks import process_uploaded_photo

import boto3

router = APIRouter(
    prefix="/photo",
    tags=["photo"]
)


@router.get("/{photo_id}/original", response_model=OriginalPhotoDownload)
async def get_original_photo(photo_id: str,
                             db: Session = Depends(get_db),
                             auth_data=Depends(JWTBearer())):
    photo = crud.photo.get_photo(db=db, photo_id=photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.author_id != auth_data['sub'] and 'photos:download_other' not in auth_data['permissions']:
        raise HTTPException(status_code=403, detail="can_only_download_own_photos")

    download_params = {
        'Bucket': S3_BUCKET,
        'Key': "/".join([S3_BUCKET_ORIGINAL_PATH, "{}_o.jpg".format(photo.id)])
    }
    download_url = boto3.client('s3').generate_presigned_url('get_object',
                                                             Params=download_params,
                                                             ExpiresIn=300)

    return OriginalPhotoDownload(download_url=download_url)


@router.post("/{photo_id}/reprocess")
async def reprocess_photo(photo_id: str,
                          db: Session = Depends(get_db),
                          auth_data=Depends(JWTBearer())):
    photo = crud.photo.get_photo(db=db, photo_id=photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.author_id != auth_data['sub'] and 'photos:reprocess_other' not in auth_data['permissions']:
        raise HTTPException(status_code=403, detail="can_only_reprocess_own_photos")

    process_uploaded_photo.process_photo(photo_data=photo, db=db)

    raise HTTPException(status_code=200, detail="processed")


@router.post("/", response_model=PhotoUpload)
async def create_upload(db: Session = Depends(get_db),
                        auth_data=Depends(JWTBearer(required_permissions=['photos:upload']))):
    author = get_author(db=db, author_id=auth_data['sub'])
    if author is None:
        raise HTTPException(status_code=500, detail="create_author_data_first")

    photo_data = PhotoCreate(author_id=auth_data['sub'])
    photo = create_photo(db=db, photo=photo_data)

    upload_url = boto3.client('s3').generate_presigned_post(
        S3_BUCKET,
        "/".join([S3_BUCKET_UPLOAD_PATH, photo.secret, "{}.jpg".format(photo.id)]),
        ExpiresIn=S3_UPLOAD_EXPIRY
    )

    photo_data = photo.__dict__
    photo_data['pre_signed_url'] = upload_url

    return photo_data


@router.put("/{photo_id}/albums", response_model=Photo)
async def replace_albums(photo_id: str,
                         album_ids: List[str],
                         db: Session = Depends(get_db),
                         auth_data=Depends(JWTBearer())):
    photo = crud.photo.get_photo(db=db, photo_id=photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.author_id != auth_data['sub'] and 'photos:manage_other' not in auth_data['permissions']:
        raise HTTPException(status_code=403, detail="can_only_manage_own_photos")

    for album_id in album_ids:
        album = get_album(db=db, album_id=album_id)
        if album is None:
            raise HTTPException(status_code=404, detail="album_not_found_{}".format(album_id))

    photo = update_photo_albums(db=db, photo=photo, album_ids=album_ids)

    return photo


@router.delete("/{photo_id}")
async def delete_photo(photo_id: str,
                       db: Session = Depends(get_db),
                       auth_data=Depends(JWTBearer())):
    photo = crud.photo.get_photo(db=db, photo_id=photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.author_id != auth_data['sub'] and 'photos:delete_other' not in auth_data['permissions']:
        raise HTTPException(status_code=403, detail="can_only_delete_own_photos")

    # if len(photo.albums) > 0:
    #     raise HTTPException(status_code=400, detail="can_only_delete_empty_event")
    action = crud.photo.delete_photo(db=db, photo=photo)
    if action:
        raise HTTPException(status_code=200, detail="photo_deleted")
    else:
        raise HTTPException(status_code=500, detail="internal_error")
