from fastapi import APIRouter, Depends, HTTPException
from auth.auth_bearer import JWTBearer

from database import sqlmodel_session
from sqlmodel import select
from typing import List

from sqlmodels.event import Event, EventCreate

import uuid

router = APIRouter(
    prefix="/event",
    tags=["events"]
)


@router.get("/", response_model=List[Event])
async def list_events():
    with sqlmodel_session:
        events = sqlmodel_session.exec(select(Event)).all()
        return events


@router.get("/{event_id}", response_model=Event)
async def get_event(event_id: str):
    with sqlmodel_session:
        event = sqlmodel_session.get(Event, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="event_not_found")
        return event


@router.post("/", response_model=Event, dependencies=[Depends(JWTBearer(required_permissions=['events:manage']))])
async def create_event(event: EventCreate):
    event = Event.from_orm(event)

    event_id = str(uuid.uuid4())
    event.id = event_id

    with sqlmodel_session:
        sqlmodel_session.add(event)
        sqlmodel_session.commit()
        sqlmodel_session.refresh(event)
        return event


@router.put("/{event_id}", response_model=Event,
            dependencies=[Depends(JWTBearer(required_permissions=['events:manage']))])
async def update_event(event_id: str, event_data: EventCreate):
    with sqlmodel_session:
        event_data = event_data.dict()
        event = sqlmodel_session.get(Event, event_id)

        if event is None:
            raise HTTPException(status_code=404, detail="event_not_found")

        for key, value in event_data.items():
            setattr(event, key, value)

        sqlmodel_session.add(event)
        sqlmodel_session.commit()
        sqlmodel_session.refresh(event)

        return event


@router.delete("/{event_id}", dependencies=[Depends(JWTBearer(required_permissions=['events:manage']))])
async def delete_event(event_id: str):
    with sqlmodel_session:
        event = sqlmodel_session.get(Event, event_id)

        if event is None:
            raise HTTPException(status_code=404, detail="event_not_found")

        if len(event.albums) > 0:
            raise HTTPException(status_code=400, detail="can_only_delete_empty_event")

        sqlmodel_session.delete(event)
        sqlmodel_session.commit()

        raise HTTPException(status_code=200, detail="event_deleted")
