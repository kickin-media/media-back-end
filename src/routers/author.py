from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.auth_bearer import JWTBearer
from dependencies import get_db
from schemas.author import AuthorCreate, Author

from crud.author import update_author_information, get_author

router = APIRouter(
    prefix="/author",
    tags=["author"]
)


@router.get("/{author_id}", response_model=Author)
async def get_author_data(author_id: str, db: Session = Depends(get_db)):
    author = get_author(db=db, author_id=author_id)

    if author is None:
        raise HTTPException(status_code=404, detail="author_not_found")

    return author


@router.put("/", response_model=Author)
async def update_author_data(author_data: AuthorCreate,
                             db: Session = Depends(get_db),
                             auth_data=Depends(JWTBearer())):
    author_data = Author(id=auth_data['sub'], name=author_data.name)
    author = update_author_information(db=db, author=author_data)

    return author