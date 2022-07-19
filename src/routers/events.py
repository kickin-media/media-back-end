from fastapi import APIRouter, Depends, HTTPException
from auth.auth_bearer import JWTBearer

from database import get_db
from sqlmodel import Session, select
from typing import List

from models.event import Event, EventCreate, EventReadList, EventReadSingle
from models.album import AlbumReadList
from models.photo import PhotoUploadPreSignedUrl

from variables import S3_BUCKET_ASSET_PATH, S3_UPLOAD_EXPIRY, S3_BUCKET, S3_PHOTO_HOSTNAME

import uuid
import boto3

router = APIRouter(
    prefix="/event",
    tags=["events"]
)


@router.get("/", response_model=List[EventReadList])
async def list_events(db: Session = Depends(get_db)):
    events = db.exec(select(Event)).all()
    return events


@router.get("/{event_id}", response_model=EventReadSingle)
async def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")
    return event


@router.get("/{event_id}/albums", response_model=List[AlbumReadList])
async def get_event_albums(event_id: str, db: Session = Depends(get_db),
                           auth_data=Depends(JWTBearer(auto_error=False))):
    include_hidden = auth_data and 'albums:read_hidden' in auth_data['permissions']

    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")

    albums = []
    for album in event.albums:
        if album.hidden_secret is not None and not include_hidden:
            continue
        albums.append(album)

    return albums


@router.post("/", response_model=Event, dependencies=[Depends(JWTBearer(required_permissions=['events:manage']))])
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    event = Event.from_orm(event)

    event_id = str(uuid.uuid4())
    event.id = event_id

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.put("/{event_id}", response_model=Event,
            dependencies=[Depends(JWTBearer(required_permissions=['events:manage']))])
async def update_event(event_id: str, event_data: EventCreate, db: Session = Depends(get_db)):
    event_data = event_data.dict()
    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")

    for key, value in event_data.items():
        setattr(event, key, value)

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


@router.delete("/{event_id}", dependencies=[Depends(JWTBearer(required_permissions=['events:manage']))])
async def delete_event(event_id: str, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")

    if len(event.albums) > 0:
        raise HTTPException(status_code=400, detail="can_only_delete_empty_event")

    db.delete(event)
    db.commit()

    raise HTTPException(status_code=200, detail="event_deleted")


# WATERMARKS


@router.get("/{event_id}/watermark")
async def get_event_watermark(event_id: str, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")

    watermark_s3_url = "/".join([
        S3_PHOTO_HOSTNAME,
        "/".join([S3_BUCKET_ASSET_PATH, "watermark-{}.png".format(event.id)])
    ])

    return watermark_s3_url


@router.post("/{event_id}/watermark", response_model=PhotoUploadPreSignedUrl,
             dependencies=[Depends(JWTBearer(required_permissions=['events:manage']))])
async def create_event_watermark_upload(event_id: str,
                                        db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")

    upload_url = boto3.client('s3').generate_presigned_post(
        S3_BUCKET,
        "/".join([S3_BUCKET_ASSET_PATH, "watermark-{}.png".format(event.id)]),
        ExpiresIn=S3_UPLOAD_EXPIRY
    )

    return upload_url


@router.delete("/{event_id}/watermark", response_model=PhotoUploadPreSignedUrl,
               dependencies=[Depends(JWTBearer(required_permissions=['events:manage']))])
async def delete_event_watermark(event_id: str,
                                 db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")

    boto3.client('s3').delete_object(
        Bucket=S3_BUCKET,
        Key="/".join([S3_BUCKET_ASSET_PATH, "watermark-{}.png".format(event.id)])
    )

    raise HTTPException(status_code=200, detail="watermark_deleted")
