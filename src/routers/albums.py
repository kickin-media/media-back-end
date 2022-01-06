from fastapi import APIRouter, Depends, HTTPException
from auth.auth_bearer import JWTBearer

from database import get_db
from sqlmodel import Session, select
from typing import List

from models.album import Album, AlbumCreate, AlbumReadList, AlbumReadSingle
from models.event import Event

import uuid

router = APIRouter(
    prefix="/album",
    tags=["albums"],
)


@router.get("/", response_model=List[AlbumReadList])
async def list_albums(db: Session = Depends(get_db)):
    albums = db.exec(select(Album)).all()
    return albums


@router.get("/{album_id}", response_model=AlbumReadSingle)
async def get_album(album_id: str, db: Session = Depends(get_db)):
    album = db.get(Album, album_id)
    if album is None:
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
async def update_album(album_id: str, album_data: AlbumCreate, db: Session = Depends(get_db)):
    album_data = album_data.dict()
    album = db.get(Album, album_id)

    if album is None:
        raise HTTPException(status_code=404, detail="album_not_found")

    event = db.get(Event, album_data['event_id'])
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")

    for key, value in album_data.items():
        setattr(album, key, value)

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
