from sqlalchemy.orm import Session
from sqlalchemy import delete
from typing import List

import models.photo as model
import schemas.photo as schema
from crud.album import get_album

import uuid
from datetime import datetime


def get_photo(db: Session, photo_id: str):
    return db.query(model.Photo).filter(model.Photo.id == photo_id).first()


def create_photo(db: Session, photo: schema.PhotoCreate):
    photo_id = str(uuid.uuid4())
    secret = str(uuid.uuid4())

    db_photo = model.Photo(id=photo_id,
                           secret=secret,
                           author_id=photo.author_id,
                           uploaded_at=datetime.utcnow(),
                           upload_processed=False)

    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    return db_photo


def update_photo_albums(db: Session, photo: model.Photo, album_ids: List[str]):
    for current_album in photo.albums:
        if current_album.id not in album_ids:
            photo.albums.remove(current_album)

    current_album_ids = [album.id for album in photo.albums]
    for album_id in album_ids:
        if album_id not in current_album_ids:
            album = get_album(db=db, album_id=album_id)
            photo.albums.append(album)

    db.commit()
    db.refresh(photo)
    return photo


def delete_photo(db: Session, photo: model.Photo):
    db.delete(photo)
    db.commit()
    return True
