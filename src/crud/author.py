from sqlalchemy.orm import Session
from sqlalchemy import update

import models.author as model
import schemas.author as schema


def update_author_information(db: Session, author: schema.Author):
    db_author = get_author(db=db, author_id=author.id)

    if db_author is None:
        db_author = model.Author(id=author.id,
                                 name=author.name)
        db.add(db_author)
        db.commit()
        db.refresh(db_author)

        return db_author

    statement = update(model.Author).where(model.Author.id == author.id).values({
        'name': author.name
    })
    db.execute(statement)
    db.commit()
    return get_author(db=db, author_id=author.id)


def get_author(db: Session, author_id: str):
    return db.query(model.Author).filter(model.Author.id == author_id).first()
