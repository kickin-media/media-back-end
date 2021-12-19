import datetime
from pydantic import BaseModel


class BatchBase(BaseModel):
    pass


class BatchCreate(BatchBase):
    pass


class Batch(BatchCreate):
    id: str
    timestamp: datetime.datetime
    expires: datetime.datetime
    presigned_url: str

    class Config:
        orm_mode = True
