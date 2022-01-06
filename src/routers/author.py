from fastapi import APIRouter, Depends, HTTPException
from auth.auth_bearer import JWTBearer

from database import get_db
from sqlmodel import Session, select

from models.author import Author, AuthorCreate, AuthorReadSingle

router = APIRouter(
    prefix="/author",
    tags=["author"]
)


@router.get("/{author_id}", response_model=AuthorReadSingle)
async def get_author_data(author_id: str, db: Session = Depends(get_db)):
    author = db.get(Author, author_id)
    if author is None:
        raise HTTPException(status_code=404, detail="author_not_found")
    return author


@router.put("/", response_model=Author)
async def update_author_data(author_data: AuthorCreate,
                             db: Session = Depends(get_db),
                             auth_data=Depends(JWTBearer())):
    author_id = auth_data['sub']
    author = db.get(Author, author_id)

    if author is None:
        author = Author(id=author_id, name=author_data.name)
    else:
        author.name = author_data.name

    db.add(author)
    db.commit()
    db.refresh(author)

    return author


@router.delete("/")
async def delete_author_data(auth_data=Depends(JWTBearer()), db: Session = Depends(get_db)):
    author_id = auth_data['sub']
    author = db.get(Author, author_id)

    if author is None:
        raise HTTPException(status_code=404, detail="author_not_found")

    if len(author.photos) > 0:
        raise HTTPException(status_code=500, detail="can_only_remove_author_without_photos")

    db.delete(author)
    db.commit()

    raise HTTPException(status_code=200, detail="author_deleted")
