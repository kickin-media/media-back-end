import datetime

from sqlalchemy import inspect
from sqlalchemy.orm import joinedload
from sqlmodel import SQLModel, Field, Relationship, Session, select
from typing import TYPE_CHECKING, Optional, List

from models.photo import Photo, PhotoReadList, PhotoReadSingle, PhotoReadSingleStub
from models.albumphotolink import AlbumPhotoLink

if TYPE_CHECKING:
    from models.event import Event, EventReadList


class AlbumBase(SQLModel):
    name: str
    timestamp: datetime.datetime
    release_time: Optional[datetime.datetime] = None
    event_id: str = Field(foreign_key="events.id")
    cover_id: Optional[str] = Field(foreign_key="photos.id", nullable=True, default=None)


class Album(AlbumBase, table=True):
    __tablename__ = "albums"

    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    hidden_secret: Optional[str] = None

    photos: List[Photo] = Relationship(back_populates="albums", link_model=AlbumPhotoLink)

    event: "Event" = Relationship(back_populates="albums")
    cover: Photo = Relationship()

    views: int = Field(default=0)

    @property
    def photos_count(self) -> int:
        # Use cached count from query subquery if available (set by listing endpoints)
        if hasattr(self, '_cached_photos_count'):
            return self._cached_photos_count
        # If photos are already eager-loaded, count them without a new query
        state = inspect(self)
        if 'photos' in state.dict:
            return len(self.photos)
        # Fallback: will trigger lazy load (should not happen on optimized endpoints)
        return len(self.photos)

    @property
    def cover_photo(self):
        if self.cover:
            return self.cover

        # Fallback cover, populated by attach_fallback_covers() where applicable
        return getattr(self, '_fallback_cover', None)


def attach_fallback_covers(db: Session, albums: List[Album]) -> None:
    """Resolve a fallback cover photo for albums that have no explicit cover.

    Costs at most two queries regardless of how many albums are passed in, and no
    queries at all when every album already has a cover set. The picked photo is
    arbitrary but stable: ordering by the link table's photo_id follows the
    (album_id, photo_id) primary key, so MySQL can stop at the first processed photo
    instead of sorting every photo in the album.
    """
    candidates = [album for album in albums if album.cover_id is None]
    if not candidates:
        return

    # Only processed photos are usable: unprocessed ones have no secret, so
    # Photo.img_urls would blow up on them.
    fallback_id_subq = (
        select(AlbumPhotoLink.photo_id)
        .join(Photo, Photo.id == AlbumPhotoLink.photo_id)
        .where(AlbumPhotoLink.album_id == Album.id, Photo.upload_processed == True)
        .correlate(Album)
        .order_by(AlbumPhotoLink.photo_id)
        .limit(1)
        .scalar_subquery()
    )

    statement = select(Album.id, fallback_id_subq).where(
        Album.id.in_([album.id for album in candidates])
    )
    fallback_ids = {album_id: photo_id for album_id, photo_id in db.execute(statement).all()}

    photo_ids = {photo_id for photo_id in fallback_ids.values() if photo_id is not None}
    if not photo_ids:
        return

    photos = db.exec(
        select(Photo).where(Photo.id.in_(photo_ids)).options(joinedload(Photo.author))
    ).unique().all()
    photos_by_id = {photo.id: photo for photo in photos}

    for album in candidates:
        album._fallback_cover = photos_by_id.get(fallback_ids.get(album.id))


class AlbumCreate(AlbumBase):
    pass


class AlbumReadList(AlbumBase):
    id: str
    photos_count: int
    cover_photo: Optional[PhotoReadSingleStub]
    hidden_secret: Optional[str]
    views: int


class AlbumReadSingleStub(AlbumReadList):
    # This should be fixed later on, but for now it throws an error I haven't yet been able to solve.
    class Event(SQLModel):
        id: str
        name: str
        timestamp: datetime.datetime

    event: Event
    # event: "EventReadList"


class AlbumReadSingle(AlbumReadSingleStub):
    photos: List[PhotoReadSingleStub]
    hidden_secret: Optional[str]


class AlbumSetSecretStatus(SQLModel):
    is_secret: bool
    refresh_secret: bool


class AlbumSetCover(SQLModel):
    photo_id: Optional[str]
