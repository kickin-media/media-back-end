from sqlalchemy.orm import Session
from sqlalchemy import update

import models.event as model
import schemas.event as schema

import uuid


def get_events(db: Session, skip: int = 0, limit: int = 100):
    return db.query(model.EventList).offset(skip).limit(limit).all()


def get_event(db: Session, event_id: str):
    return db.query(model.Event).filter(model.Event.id == event_id).first()


def create_event(db: Session, event: schema.EventCreate):
    event_id = str(uuid.uuid4())
    db_event = model.Event(id=event_id,
                           name=event.name,
                           timestamp=event.timestamp)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def update_event(db: Session, event: model.Event, event_data: schema.EventCreate):
    statement = update(model.Event).where(model.Event.id == event.id).values(event_data.dict())
    db.execute(statement)
    db.commit()
    return get_event(db=db, event_id=event.id)


def delete_event(db: Session, event: model.Event):
    db.delete(event)
    db.commit()
    return True
