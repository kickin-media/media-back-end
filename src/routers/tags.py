from fastapi import APIRouter, Depends
from database import get_db
from sqlmodel import Session, select
from typing import List

from models.tag import Tag, TagReadList

router = APIRouter(
    prefix="/tag",
    tags=["tags"]
)


@router.get("/", response_model=List[TagReadList])
async def list_tags(db: Session = Depends(get_db)):
    tags = db.exec(select(Tag)).all()
    return tags
