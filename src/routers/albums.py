import datetime

from fastapi import APIRouter, Depends, HTTPException
from auth.auth_bearer import JWTBearer

from database import get_db
from sqlmodel import Session, select
from typing import List

from models.album import Album, AlbumCreate, AlbumReadList, AlbumReadSingle, AlbumSetSecretStatus, AlbumSetCover, \
    AlbumReadSingleStub
from models.event import Event
from models.photo import Photo

import uuid

router = APIRouter(
    prefix="/album",
    tags=["albums"],
)


@router.get("/", response_model=List[AlbumReadList],
            dependencies=[Depends(JWTBearer(required_permissions=['albums:manage']))])
async def list_albums(db: Session = Depends(get_db)):
    albums = db.exec(select(Album)).all()
    return albums


@router.get("/{album_id}", response_model=AlbumReadSingle)
async def get_album(album_id: str, secret: str = None, db: Session = Depends(get_db),
                    auth_data=Depends(JWTBearer(auto_error=False))):
    include_hidden = auth_data and 'albums:read_hidden' in auth_data['permissions']

    album = db.get(Album, album_id)

    if album is None:
        raise HTTPException(status_code=404, detail="album_not_found")

    # Determine if we can show the photos in this album if it's a timed album.
    if album.release_time is not None:
        if not include_hidden:
            if datetime.datetime.utcnow() < album.release_time:
                album.photos = []

    # Determine if we can show this album at all if it's a hidden album.
    if album.hidden_secret is not None:
        if include_hidden:
            return album
        if secret is not None and secret == album.hidden_secret:
            return album
        raise HTTPException(status_code=404, detail="album_not_found")

    return album


@router.post("/", response_model=Album, dependencies=[Depends(JWTBearer(required_permissions=['albums:manage']))])
async def create_album(album: AlbumCreate, db: Session = Depends(get_db)):
    event = db.get(Event, album.event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")

    album = Album.from_orm(album)

    album_id = str(uuid.uuid4())
    album.id = album_id

    db.add(album)
    db.commit()
    db.refresh(album)

    return album


@router.put("/{album_id}", response_model=Album,
            dependencies=[Depends(JWTBearer(required_permissions=['albums:manage']))])
async def update_album(album_id: str, album: AlbumCreate, db: Session = Depends(get_db)):
    db_album = db.get(Album, album_id)

    if db_album is None:
        raise HTTPException(status_code=404, detail="album_not_found")

    event = db.get(Event, album.event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")

    for key, value in album.dict().items():
        setattr(db_album, key, value)

    db.add(db_album)
    db.commit()
    db.refresh(db_album)

    return db_album


@router.put("/{album_id}/hidden", response_model=AlbumReadSingleStub,
            dependencies=[Depends(JWTBearer(required_permissions=['albums:manage']))])
async def update_album_hidden_status(album_id: str, hidden_status: AlbumSetSecretStatus,
                                     db: Session = Depends(get_db)):
    album = db.get(Album, album_id)

    if album is None:
        raise HTTPException(status_code=404, detail="album_not_found")

    if hidden_status.is_secret:
        if album.hidden_secret is None or hidden_status.refresh_secret:
            album_secret = str(uuid.uuid4())
            album.hidden_secret = album_secret
    else:
        album.hidden_secret = None

    db.add(album)
    db.commit()
    db.refresh(album)

    return album


@router.put("/{album_id}/cover", response_model=AlbumReadSingleStub,
            dependencies=[Depends(JWTBearer(required_permissions=['albums:manage']))])
async def update_album_cover(album_id: str, cover_info: AlbumSetCover,
                             db: Session = Depends(get_db)):
    album = db.get(Album, album_id)
    if album is None:
        raise HTTPException(status_code=404, detail="album_not_found")

    if cover_info.photo_id is None:
        album.cover = None

    else:
        photo = db.get(Photo, cover_info.photo_id)
        if photo is None:
            raise HTTPException(status_code=404, detail="photo_not_found")

        if not photo.upload_processed:
            raise HTTPException(status_code=500, detail="photo_not_processed")

        if album not in photo.albums:
            raise HTTPException(status_code=500, detail="photo_not_in_album")
        album.cover = photo

    db.add(album)
    db.commit()
    db.refresh(album)

    return album


@router.delete("/{album_id}/empty", response_model=AlbumReadSingleStub,
               dependencies=[Depends(JWTBearer(required_permissions=['albums:manage']))])
async def empty_album(album_id: str, db: Session = Depends(get_db)):
    db_album = db.get(Album, album_id)

    if db_album is None:
        raise HTTPException(status_code=404, detail="album_not_found")

    db_album_photos = db_album.photos
    photo_ids_to_remove = []
    for photo in db_album_photos:
        photo_ids_to_remove.append(photo.id)

    for photo_id in photo_ids_to_remove:
        photo = db.get(Photo, photo_id)
        photo.albums.remove(db_album)
        db.add(photo)

    db.commit()
    db.refresh(db_album)

    return db_album


@router.delete("/{album_id}", dependencies=[Depends(JWTBearer(required_permissions=['albums:manage']))])
async def delete_album(album_id: str, db: Session = Depends(get_db)):
    album = db.get(Album, album_id)

    if album is None:
        raise HTTPException(status_code=404, detail="album_not_found")

    if len(album.photos) > 0:
        raise HTTPException(status_code=400, detail="can_only_delete_empty_albums")

    db.delete(album)
    db.commit()

    return HTTPException(status_code=200, detail="album_deleted")
