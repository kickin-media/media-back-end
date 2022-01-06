from fastapi import APIRouter, Depends, HTTPException
from auth.auth_bearer import JWTBearer
from sqlalchemy.orm import Session
from typing import List

from dependencies import get_db
import crud.album
import crud.event
from schemas.album import Album, AlbumCreate

router = APIRouter(
    prefix="/album",
    tags=["albums"]
)


@router.get("/", response_model=List[Album])
async def list_albums(db: Session = Depends(get_db)):
    return crud.album.get_albums(db=db)


@router.get("/{album_id}", response_model=Album)
async def get_album(album_id: str, db: Session = Depends(get_db)):
    album = crud.album.get_album(db=db, album_id=album_id)
    if album is None:
        raise HTTPException(status_code=404, detail="album_not_found")
    return album


@router.post("/", response_model=Album, dependencies=[Depends(JWTBearer(required_permissions=['albums:manage']))])
async def create_album(album: AlbumCreate, db: Session = Depends(get_db)):
    event = crud.event.get_event(db=db, event_id=album.event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")

    album = crud.album.create_album(db=db, album=album)
    return album


@router.put("/{album_id}", response_model=Album, dependencies=[Depends(JWTBearer(required_permissions=['albums:manage']))])
async def update_album(album_id: str, album_data: AlbumCreate, db: Session = Depends(get_db)):
    album = crud.album.get_album(db=db, album_id=album_id)
    if album is None:
        raise HTTPException(status_code=404, detail="album_not_found")

    event = crud.event.get_event(db=db, event_id=album_data.event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")

    new_album = crud.album.update_album(db=db, album=album, album_data=album_data)
    return new_album


@router.delete("/{album_id}", dependencies=[Depends(JWTBearer(required_permissions=['albums:manage']))])
async def delete_album(album_id: str, db: Session = Depends(get_db)):
    album = crud.album.get_album(db=db, album_id=album_id)
    if album is None:
        raise HTTPException(status_code=404, detail="album_not_found")
    action = crud.album.delete_album(db=db, album=album)
    if action:
        raise HTTPException(status_code=200, detail="album_deleted")
    else:
        raise HTTPException(status_code=500, detail="internal_error")
