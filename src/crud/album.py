from sqlalchemy.orm import Session, joinedload
from sqlalchemy import update

import models.album as model
import schemas.album as schema

import uuid


def get_albums(db: Session, skip: int = 0, limit: int = 100):
    return db.query(model.Album).offset(skip).limit(limit).all()


def get_album(db: Session, album_id: str):
    return db.query(model.Album).filter(model.Album.id == album_id).options(joinedload(model.Album.photos)).first()


def create_album(db: Session, album: schema.AlbumCreate):
    album_id = str(uuid.uuid4())
    db_album = model.Album(id=album_id,
                           name=album.name,
                           timestamp=album.timestamp,
                           event_id=album.event_id)
    db.add(db_album)
    db.commit()
    db.refresh(db_album)
    return db_album


def update_album(db: Session, album: model.Album, album_data: schema.AlbumCreate):
    statement = update(model.Album).where(model.Album.id == album.id).values(album_data.dict())
    db.execute(statement)
    db.commit()
    return get_album(db=db, album_id=album.id)


def delete_album(db: Session, album: model.Album):
    db.delete(album)
    db.commit()
    return True
