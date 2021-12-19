from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from auth.auth_bearer import JWTBearer
from dependencies import get_db
import crud.event
from schemas.upload import Batch, BatchCreate

router = APIRouter(
    prefix="/upload",
    tags=["upload"]
)


@router.post("/", response_model=Batch)
async def create_batch(db: Session = Depends(get_db), scopes=Depends(JWTBearer())):
    # event = crud.event.create_event(db=db)
    # return event
    return {}
