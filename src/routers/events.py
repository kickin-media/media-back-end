from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from dependencies import get_db
import crud.event
from schemas.event import Event, EventCreate

router = APIRouter(
    prefix="/event",
    tags=["events"]
)


@router.get("/", response_model=List[Event])
async def list_events(db: Session = Depends(get_db)):
    return crud.event.get_events(db=db)


@router.get("/{event_id}", response_model=Event)
async def get_event(event_id: str, db: Session = Depends(get_db)):
    event = crud.event.get_event(db=db, event_id=event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")
    return event


@router.post("/", response_model=Event)
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    event = crud.event.create_event(db=db, event=event)
    return event


@router.put("/{event_id}", response_model=Event)
async def update_event(event_id: str, event_data: EventCreate, db: Session = Depends(get_db)):
    event = crud.event.get_event(db=db, event_id=event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")
    new_event = crud.event.update_event(db=db, event=event, event_data=event_data)
    return new_event


@router.delete("/{event_id}")
async def delete_event(event_id: str, db: Session = Depends(get_db)):
    event = crud.event.get_event(db=db, event_id=event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event_not_found")
    action = crud.event.delete_event(db=db, event=event)
    if action:
        raise HTTPException(status_code=200, detail="event_deleted")
    else:
        raise HTTPException(status_code=500, detail="internal_error")
