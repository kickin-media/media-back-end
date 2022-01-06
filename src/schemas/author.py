from pydantic import BaseModel


class AuthorBase(BaseModel):
    pass


class AuthorCreate(AuthorBase):
    name: str


class Author(AuthorCreate):
    id: str

    class Config:
        orm_mode = True
