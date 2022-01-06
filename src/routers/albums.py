import datetime

from fastapi import APIRouter, Depends, HTTPException
from auth.auth_bearer import JWTBearer

from database import get_db
from sqlmodel import Session, select
from typing import List

from models.album import Album, AlbumCreate, AlbumReadList, AlbumReadSingle, AlbumSetSecretStatus
from models.event import Event

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


def get_album(album_id: str, db: Session = Depends(get_db),
              include_hidden: bool = False, provided_secret: str = None):
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
        if provided_secret is not None and provided_secret == album.hidden_secret:
            return album
        raise HTTPException(status_code=404, detail="album_not_found")

    return album


@router.get("/{album_id}", response_model=AlbumReadSingle)
async def get_album_unauthenticated(album_id: str, secret: str = None, db: Session = Depends(get_db)):
    return get_album(album_id=album_id, db=db, provided_secret=secret)


@router.get("/{album_id}/authenticated", response_model=AlbumReadSingle)
async def get_album_authenticated(album_id: str, secret: str = None, db: Session = Depends(get_db),
                                  auth_data=Depends(JWTBearer())):
    include_hidden = 'albums:read_hidden' in auth_data['permissions']
    return get_album(album_id=album_id, db=db, include_hidden=include_hidden, provided_secret=secret)


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


@router.put("/{album_id}/hidden", response_model=Album,
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
