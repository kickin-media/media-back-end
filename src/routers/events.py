from fastapi import APIRouter, Depends, HTTPException
from auth.auth_bearer import JWTBearer

from database import get_db
from sqlmodel import Session, select
from typing import List

from models.event import Event, EventCreate, EventReadList, EventReadSingle

import uuid

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
