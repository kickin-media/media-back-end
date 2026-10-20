import datetime
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from auth.auth_bearer import JWTBearer
from dateutil import parser
from sqlalchemy import update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import joinedload, selectinload

from database import get_db
from sqlmodel import Session, select
from typing import List, Optional

from models.photo import Photo, OriginalPhotoDownload, PhotoUploadResponse, PhotoReadSingle, PhotoReadSingleStub, \
    PhotoStream, PhotoReadList, PhotoUploadRequest, PhotoChecksum, PhotoChecksumResult
from models.author import Author
from models.album import Album, attach_fallback_covers
from models.albumphotolink import AlbumPhotoLink
from models.event import Event, EventReadSingle
from models.tag import Tag, TagRequest, PhotoTagRead
from models.tagphotolink import TagPhotoLink

from variables import S3_BUCKET, S3_UPLOAD_EXPIRY, S3_BUCKET_UPLOAD_PATH, S3_BUCKET_ORIGINAL_PATH, S3_BUCKET_PHOTO_PATH, \
    PHOTO_PROCESSING_SQS_QUEUE, API_BASE, SITEWIDE_PASSWORD

import base64
import boto3
import botocore.exceptions
import uuid
import json
import re

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 0.5


def _execute_with_retry(db: Session, statement, max_retries=MAX_RETRIES):
    """Execute a statement with retry on transient MySQL errors (lock timeout, deadlock)."""
    return _transaction_with_retry(db, lambda: db.execute(statement), max_retries)


def _transaction_with_retry(db: Session, work, max_retries=MAX_RETRIES):
    """Run `work` and commit, retrying the whole transaction on transient MySQL errors (lock timeout, deadlock)."""
    for attempt in range(max_retries):
        try:
            result = work()
            db.commit()
            return result
        except OperationalError as e:
            db.rollback()
            mysql_error_code = e.orig.args[0] if e.orig else None
            if mysql_error_code in (1205, 1213) and attempt < max_retries - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    "Transient DB error (code %s) on attempt %d/%d, retrying in %.1fs",
                    mysql_error_code, attempt + 1, max_retries, delay
                )
                time.sleep(delay)
                continue
            raise


def photo_event_id(photo: Photo) -> Optional[str]:
    """A photo belongs to the event of its albums. Same rule as `get_photo_event`."""
    if len(photo.albums) == 0:
        return None
    return photo.albums[0].event_id


def lock_event(db: Session, event_id: str) -> Event:
    """Lock the event row so duplicate checks within one event run one at a time."""
    return db.exec(select(Event).where(Event.id == event_id).with_for_update()).first()


def find_event_duplicate(db: Session, event_id: str, content_hash: str,
                         exclude_photo_id: Optional[str] = None) -> Optional[Photo]:
    statement = select(Photo). \
        join(AlbumPhotoLink, AlbumPhotoLink.photo_id == Photo.id). \
        join(Album, Album.id == AlbumPhotoLink.album_id). \
        where(Album.event_id == event_id, Photo.content_hash == content_hash). \
        order_by(Photo.uploaded_at).limit(1)
    if exclude_photo_id is not None:
        statement = statement.where(Photo.id != exclude_photo_id)
    # A locking read sees the latest committed hashes, which a plain read inside the same transaction might not.
    return db.exec(statement.with_for_update(read=True)).first()


def add_photo_to_album(photo: Photo, album: Album, event: Event) -> bool:
    """Add a photo to an album of its own event. Returns whether the photo is in the album afterwards."""
    if album in photo.albums:
        return True
    current_event_id = photo_event_id(photo)
    if current_event_id is not None and current_event_id != album.event_id:
        return False
    if event.locked:
        return False
    photo.albums.append(album)
    return True


def merge_duplicate(db: Session, duplicate: Photo, existing: Photo, event: Event):
    """Move the albums of a duplicate upload to the existing photo and delete the duplicate."""
    for album in list(duplicate.albums):
        add_photo_to_album(existing, album, event)
        if album.cover_id == duplicate.id:
            album.cover_id = existing.id
            db.add(album)

    for link in db.exec(select(TagPhotoLink).where(TagPhotoLink.photo_id == duplicate.id)).all():
        db.delete(link)

    duplicate.albums = []
    db.add(existing)
    db.delete(duplicate)


router = APIRouter(
    prefix="/photo",
    tags=["photo"]
)


@router.get("/stream", response_model=PhotoStream)
def get_event_photo_stream(timestamp: str = None, photo_id_start: str = 'ffffffff-ffff-ffff-ffff-ffffffffffff',
                                 direction: str = 'older', sort_by: str = 'uploaded',
                                 db: Session = Depends(get_db)):
    page_size = 50

    datetime_pattern = r"[0-9]{4}\-[0-9]{2}\-[0-9]{2}\s[0-2][0-9]:[0-5][0-9]:[0-5][0-9]"
    datetime_regex = re.compile(datetime_pattern)
    unix_pattern = r"[0-9]+"
    unix_regex = re.compile(unix_pattern)

    if timestamp is None:
        timestamp = datetime.datetime.now()
    elif re.fullmatch(datetime_regex, timestamp):
        timestamp = parser.parse(timestamp)
    elif re.fullmatch(unix_regex, timestamp):
        timestamp = datetime.datetime.fromtimestamp(int(timestamp))
    else:
        raise HTTPException(status_code=400, detail="invalid_timestamp")

    if sort_by == 'taken':
        sorting_key = Photo.timestamp
    elif sort_by == 'uploaded':
        sorting_key = Photo.uploaded_at
    else:
        # if you add extra cases, don't forget to also change the if-else statement
        # in the `for photo in photostream_results` loop
        raise HTTPException(status_code=400, detail="invalid_sort_by")

    photostream_statement = select(Photo)

    if direction == 'older':
        photostream_statement = photostream_statement. \
            where((sorting_key < timestamp) | ((sorting_key == timestamp) & (Photo.id < photo_id_start))). \
            order_by(sorting_key.desc()).order_by(Photo.id.desc()).limit(page_size)
    elif direction == 'newer':
        photostream_statement = photostream_statement. \
            where((sorting_key > timestamp) | ((sorting_key == timestamp) & (Photo.id < photo_id_start))). \
            order_by(sorting_key.asc()).order_by(Photo.id.desc()).limit(page_size)
    else:
        raise HTTPException(status_code=400, detail="invalid_direction")

    photostream_statement = photostream_statement.options(selectinload(Photo.albums))

    photostream_results = db.exec(photostream_statement)

    photostream_response = PhotoStream(
        photos=[],
        next_timestamp="",
        next_photo_id=""
    )

    for photo in photostream_results:
        photostream_response.next_timestamp = str(photo.timestamp if sort_by == 'taken' else photo.uploaded_at)
        photostream_response.next_photo_id = photo.id
        visible = True
        for album in photo.albums:
            if album.hidden_secret is None:
                visible = True
                break
            if album.release_time is None or datetime.datetime.now() > album.release_time:
                visible = True
                break
        if visible:
            # These yucky lines are necessary because img_urls is a computed property and for some reason not
            # automatically included in the JSON response in this specific case...
            # See: https://github.com/tiangolo/fastapi/issues/4288
            photo_with_urls = photo.dict()
            photo_with_urls['img_urls'] = photo.img_urls
            photostream_response.photos.append(photo_with_urls)

    photostream_response.next_photo_id = photostream_response.next_photo_id.split("-")[0]

    return photostream_response


@router.get("/unprocessed", response_model=List[PhotoReadList],
            dependencies=[Depends(JWTBearer(required_permissions=['system:admin']))])
def get_unprocessed_photos(db: Session = Depends(get_db)):
    photos = db.query(Photo).filter(Photo.upload_processed == False).all()
    return [p for p in photos]


@router.get("/{photo_id}", response_model=PhotoReadSingle)
def get_photo(photo_id: str,
                    db: Session = Depends(get_db)):
    statement = select(Photo).where(Photo.id == photo_id).options(
        selectinload(Photo.albums),
        joinedload(Photo.author)
    )
    photo = db.exec(statement).unique().first()

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    attach_fallback_covers(db, photo.albums)

    photo_dict = photo.dict()
    photo_dict['img_urls'] = photo.img_urls
    photo_dict['exif'] = photo.exif
    photo_dict['gps_thumb'] = photo.gps_thumb
    photo_dict['albums'] = photo.albums
    photo_dict['author'] = photo.author
    photo_dict['tags'] = get_photo_tags(db, photo_id)

    return photo_dict


def is_photo_visible(photo: Photo, include_hidden: bool) -> bool:
    for album in photo.albums:
        if album.hidden_secret is not None and not include_hidden:
            continue
        if album.release_time is not None and datetime.datetime.now() < album.release_time and not include_hidden:
            continue
        return True
    return False


def get_photo_tags(db: Session, photo_id: str) -> list:
    statement = select(TagPhotoLink).where(TagPhotoLink.photo_id == photo_id)
    results = db.exec(statement).all()
    tags = []
    for link in results:
        tags.append(PhotoTagRead(
            tag_slug=link.tag_slug,
            tag_value=link.tag_value if link.tag_value != "" else None
        ))
    return tags


@router.post("/{photo_id}/tags", response_model=List[PhotoTagRead])
def add_photo_tags(photo_id: str, tag_requests: List[TagRequest],
                         db: Session = Depends(get_db),
                         auth_data=Depends(JWTBearer(required_permissions=['photos:tagging']))):
    photo = db.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    include_hidden = 'albums:read_hidden' in auth_data['permissions']
    if not is_photo_visible(photo, include_hidden):
        raise HTTPException(status_code=404, detail="photo_not_found")

    for tag_request in tag_requests:
        tag = db.exec(select(Tag).where(Tag.tag_slug == tag_request.tag)).first()
        if tag is None:
            raise HTTPException(status_code=404, detail="tag_not_found_{}".format(tag_request.tag))

        if not tag.supports_value and tag_request.value is not None:
            raise HTTPException(status_code=400, detail="tag_does_not_support_values_{}".format(tag_request.tag))

        if tag.supports_value and tag_request.value is None:
            raise HTTPException(status_code=400, detail="tag_requires_value_{}".format(tag_request.tag))

        tag_value = tag_request.value if tag_request.value is not None else ""

        existing = db.exec(select(TagPhotoLink).where(
            TagPhotoLink.tag_slug == tag.tag_slug,
            TagPhotoLink.photo_id == photo_id,
            TagPhotoLink.tag_value == tag_value
        )).first()
        if existing is not None:
            continue

        link = TagPhotoLink(tag_slug=tag.tag_slug, photo_id=photo_id, tag_value=tag_value)
        db.add(link)

    db.commit()
    return get_photo_tags(db, photo_id)


@router.post("/{photo_id}/tags/remove", response_model=List[PhotoTagRead])
def remove_photo_tags(photo_id: str, tag_requests: List[TagRequest],
                            db: Session = Depends(get_db),
                            auth_data=Depends(JWTBearer(required_permissions=['photos:tagging']))):
    photo = db.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    include_hidden = 'albums:read_hidden' in auth_data['permissions']
    if not is_photo_visible(photo, include_hidden):
        raise HTTPException(status_code=404, detail="photo_not_found")

    for tag_request in tag_requests:
        tag = db.exec(select(Tag).where(Tag.tag_slug == tag_request.tag)).first()
        if tag is None:
            raise HTTPException(status_code=404, detail="tag_not_found_{}".format(tag_request.tag))

        tag_value = tag_request.value if tag_request.value is not None else ""

        existing = db.exec(select(TagPhotoLink).where(
            TagPhotoLink.tag_slug == tag.tag_slug,
            TagPhotoLink.photo_id == photo_id,
            TagPhotoLink.tag_value == tag_value
        )).first()
        if existing is not None:
            db.delete(existing)

    db.commit()
    return get_photo_tags(db, photo_id)


@router.get("/{photo_id}/event", response_model=EventReadSingle)
def get_photo_event(photo_id: str,
                          db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if len(photo.albums) == 0:
        raise HTTPException(status_code=404, detail="photo_not_in_album")

    return photo.albums[0].event


@router.post("/{photo_id}/checksum/{photo_exif_secret}", response_model=PhotoChecksumResult)
def register_checksum(photo_id: str, photo_exif_secret: str, checksum: PhotoChecksum,
                      db: Session = Depends(get_db)):
    """Called by the processing Lambda with the hash of the uploaded file, before it processes the photo."""

    def work():
        photo = db.get(Photo, photo_id)

        if photo is None:
            raise HTTPException(status_code=404, detail="photo_not_found")

        if photo.exif_update_secret is None:
            raise HTTPException(status_code=403, detail="photo_doesnt_expect_update")

        if photo_exif_secret != photo.exif_update_secret:
            raise HTTPException(status_code=403, detail="invalid_update_key")

        if photo.content_hash == checksum.sha256:
            return PhotoChecksumResult(status="unique")

        event_id = photo_event_id(photo)
        if event_id is None:
            raise HTTPException(status_code=409, detail="photo_not_in_album")

        event = lock_event(db, event_id)
        existing = find_event_duplicate(db, event_id, checksum.sha256, exclude_photo_id=photo.id)

        if existing is None:
            photo.content_hash = checksum.sha256
            db.add(photo)
            return PhotoChecksumResult(status="unique")

        merge_duplicate(db, duplicate=photo, existing=existing, event=event)
        return PhotoChecksumResult(status="duplicate", duplicate_of=existing.id)

    result = _transaction_with_retry(db, work)
    if result.status == "duplicate":
        logger.info("Discarded upload %s as a duplicate of %s", photo_id, result.duplicate_of)
    return result


@router.post("/{photo_id}/exif/{photo_exif_secret}")
def finalize_upload(photo_id: str, photo_exif_secret: str, request_data: dict,
                          db: Session = Depends(get_db)):
    photo = db.exec(
        select(Photo.id, Photo.exif_update_secret).where(Photo.id == photo_id)
    ).first()

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.exif_update_secret is None:
        raise HTTPException(status_code=403, detail="photo_doesnt_expect_update")

    if photo_exif_secret != photo.exif_update_secret:
        raise HTTPException(status_code=403, detail="invalid_update_key")

    exif_data = request_data['exif_data']

    update_values = {
        "exif_data": json.dumps(exif_data),
        "upload_processed": True,
        "exif_update_secret": None,
    }

    if 'datetime_original' in exif_data:
        datetime_original = exif_data['datetime_original']
        try:
            update_values["timestamp"] = datetime.datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S')
        except (ValueError, TypeError):
            update_values["timestamp"] = None

    gps_data = request_data['gps_data']
    if gps_data is not None:
        update_values["gps_lat"] = gps_data[0]
        update_values["gps_lon"] = gps_data[1]

    result = _execute_with_retry(db,
        update(Photo)
        .where(Photo.id == photo_id)
        .where(Photo.exif_update_secret == photo_exif_secret)
        .values(**update_values)
    )

    if result.rowcount == 0:
        raise HTTPException(status_code=409, detail="photo_already_finalized")

    raise HTTPException(status_code=200, detail="done")


@router.get("/{photo_id}/original", response_model=OriginalPhotoDownload)
def get_original_photo(photo_id: str,
                             auth_data=Depends(JWTBearer()),
                             db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.author.id != auth_data['sub'] and 'photos:download_other' not in auth_data['permissions']:
        raise HTTPException(status_code=403, detail="can_only_download_own_photos")

    download_params = {
        'Bucket': S3_BUCKET,
        'Key': "/".join([S3_BUCKET_ORIGINAL_PATH, "{}_o.jpg".format(photo.id)])
    }
    download_url = boto3.client('s3').generate_presigned_url('get_object',
                                                             Params=download_params,
                                                             ExpiresIn=300)

    return OriginalPhotoDownload(download_url=download_url)


@router.get("/{photo_id}/original_upload", response_model=OriginalPhotoDownload,
            dependencies=[Depends(JWTBearer(required_permissions=['system:admin']))])
def get_original_photo_upload(photo_id: str, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    download_params = {
        'Bucket': S3_BUCKET,
        'Key': "/".join([S3_BUCKET_UPLOAD_PATH, photo.secret, "{}.jpg".format(photo.id)])
    }
    download_url = boto3.client('s3').generate_presigned_url('get_object',
                                                             Params=download_params,
                                                             ExpiresIn=300)

    return OriginalPhotoDownload(download_url=download_url)


def trigger_photo_process(photo: Photo, exif_update_secret: str, author: Author, source_path: str,
                          delete_upload: bool = False, delay_seconds: int = 60, ttl: int = 30,
                          check_duplicate: bool = False):
    sqs = boto3.client('sqs')

    data = {
        'TTL': ttl,
        'S3_BUCKET': S3_BUCKET,
        'S3_SOURCE_PATH': source_path,
        'S3_BUCKET_PHOTO_PATH': S3_BUCKET_PHOTO_PATH,
        'S3_BUCKET_ORIGINAL_PATH': S3_BUCKET_ORIGINAL_PATH,
        'API_BASE': API_BASE
    }

    # If a sitewide password is configured, pass it (base64-encoded, ready to use as the
    # X-Sitewide-Password header) so the Lambda can authenticate its API callbacks.
    if SITEWIDE_PASSWORD is not None:
        data['SITEWIDE_PASSWORD'] = base64.b64encode(
            SITEWIDE_PASSWORD.encode('utf-8')).decode('utf-8')

    sqs_message_body = json.dumps({
        'photo_id': photo.id,
        'photo_secret': photo.secret,
        'exif_update_secret': exif_update_secret,
        'author': author.name,
        'delete_upload': delete_upload,
        'check_duplicate': check_duplicate,
        'data': data
    })

    sqs.send_message(
        QueueUrl=PHOTO_PROCESSING_SQS_QUEUE,
        MessageBody=sqs_message_body,
        DelaySeconds=delay_seconds,
    )


@router.post("/{photo_id}/reprocess")
def reprocess_photo(photo_id: str,
                          auth_data=Depends(JWTBearer()),
                          db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.author.id != auth_data['sub'] and 'photos:manage_other' not in auth_data['permissions']:
        raise HTTPException(status_code=403, detail="can_only_reprocess_own_photos")

    exif_update_secret = str(uuid.uuid4())
    photo.exif_update_secret = exif_update_secret
    db.add(photo)
    db.commit()

    original_path = "/".join([S3_BUCKET_ORIGINAL_PATH, "{}_o.jpg".format(photo.id)])
    upload_path = "/".join([S3_BUCKET_UPLOAD_PATH, photo.secret, "{}.jpg".format(photo.id)])

    # Check if the original exists; if not, fall back to the upload path.
    # Uses head_object which requires s3:ListBucket for proper NoSuchKey errors.
    # Without ListBucket, S3 returns 403 instead of 404 for missing keys.
    s3 = boto3.client('s3')

    def s3_object_exists(key):
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=key)
            return True
        except botocore.exceptions.ClientError as err:
            if err.response['Error']['Code'] in ('404', '403'):
                return False
            raise

    if s3_object_exists(original_path):
        source_path = original_path
        delete_upload = False
    elif s3_object_exists(upload_path):
        source_path = upload_path
        delete_upload = True
    else:
        raise HTTPException(status_code=404, detail="photo_source_not_found")

    trigger_photo_process(photo=photo, author=photo.author, exif_update_secret=exif_update_secret,
                          delete_upload=delete_upload, source_path=source_path, delay_seconds=0, ttl=5)

    raise HTTPException(status_code=200, detail="scheduled")


def _new_upload(author_id: str):
    """Create a photo record and a pre-signed S3 upload URL for it. Does not add or commit the record."""
    exif_update_secret = str(uuid.uuid4())

    photo = Photo(
        id=str(uuid.uuid4()),
        secret=str(uuid.uuid4()),
        uploaded_at=datetime.datetime.now(),
        upload_processed=False,
        author_id=author_id,
        exif_update_secret=exif_update_secret
    )

    upload_url = boto3.client('s3').generate_presigned_post(
        S3_BUCKET,
        "/".join([S3_BUCKET_UPLOAD_PATH, photo.secret, "{}.jpg".format(photo.id)]),
        ExpiresIn=S3_UPLOAD_EXPIRY
    )

    return photo, exif_update_secret, upload_url


@router.post("/", response_model=List[PhotoUploadResponse])
def create_upload(num_uploads: int = 1,
                        upload_request: Optional[PhotoUploadRequest] = None,
                        auth_data=Depends(JWTBearer(required_permissions=['photos:upload'])),
                        db: Session = Depends(get_db)):
    # Clients that send `upload_request` get duplicates filtered out before uploading. The response then has one entry
    # per file, in request order. Duplicates have no upload URL and refer to the existing photo, which is added to the
    # requested album. Clients without a body get `num_uploads` upload URLs, as before.
    if upload_request is not None:
        num_uploads = len(upload_request.files)

    # If this limit is ever changed, it needs to be updated in the front-end as well!
    if num_uploads < 1 or num_uploads > 500:
        raise HTTPException(status_code=400, detail="max_number_of_uploads_in_one_batch")

    author_id = auth_data['sub']
    author = db.get(Author, author_id)
    if author is None:
        raise HTTPException(status_code=400, detail="create_author_data_first")

    def work():
        response_list = []
        photos_to_process = []

        if upload_request is None:
            hashes = [None] * num_uploads
            album = event = None
        else:
            hashes = [file.sha256 for file in upload_request.files]
            album = db.get(Album, upload_request.album_id)
            if album is None:
                raise HTTPException(status_code=404, detail="album_not_found")
            event = lock_event(db, album.event_id)

        new_photo_ids = {}
        for content_hash in hashes:
            if content_hash is not None:
                if content_hash in new_photo_ids:
                    response_list.append(PhotoUploadResponse(photo_id=new_photo_ids[content_hash], duplicate=True))
                    continue

                existing = find_event_duplicate(db, album.event_id, content_hash)
                if existing is not None:
                    add_photo_to_album(existing, album, event)
                    db.add(existing)
                    response_list.append(PhotoUploadResponse(photo_id=existing.id, duplicate=True))
                    continue

            photo, exif_update_secret, upload_url = _new_upload(author_id)
            db.add(photo)

            if content_hash is not None:
                new_photo_ids[content_hash] = photo.id

            response_list.append(PhotoUploadResponse(
                photo_id=photo.id,
                pre_signed_url=upload_url
            ))

            photos_to_process.append((photo, exif_update_secret, upload_url['fields']['key']))

        return response_list, photos_to_process

    response_list, photos_to_process = _transaction_with_retry(db, work)

    for photo, exif_update_secret, source_path in photos_to_process:
        trigger_photo_process(photo=photo, author=author, exif_update_secret=exif_update_secret, delete_upload=True,
                              source_path=source_path, check_duplicate=True)

    return response_list


@router.put("/{photo_id}/albums", response_model=PhotoReadSingleStub)
def replace_albums(photo_id: str,
                         album_ids: List[str],
                         db: Session = Depends(get_db),
                         auth_data=Depends(JWTBearer())):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.author.id != auth_data['sub'] and 'photos:manage_other' not in auth_data['permissions']:
        raise HTTPException(status_code=403, detail="can_only_manage_own_photos")

    current_album_ids = [album.id for album in photo.albums]
    albums = []
    for album_id in album_ids:
        album = db.get(Album, album_id)
        if album is None:
            raise HTTPException(status_code=404, detail="album_not_found_{}".format(album_id))
        if album.id not in current_album_ids:
            if album.event.locked:
                raise HTTPException(status_code=403,
                                    detail="cannot_add_to_album_{album_id}_event_{event_id}_locked".format(
                                        album_id=album.id, event_id=album.event.id))
        albums.append(album)

    if len({album.event_id for album in albums}) > 1:
        raise HTTPException(status_code=400, detail="albums_must_share_event")

    for album in photo.albums:
        if album.id not in album_ids:
            if album.cover_id == photo.id:
                album.cover_id = None
                db.add(album)
                db.commit()
                db.refresh(album)

    photo.albums = albums
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return photo


@router.delete("/{photo_id}")
def delete_photo(photo_id: str,
                       db: Session = Depends(get_db),
                       auth_data=Depends(JWTBearer())):
    photo = db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="photo_not_found")

    if photo.author.id != auth_data['sub'] and 'photos:delete_other' not in auth_data['permissions']:
        raise HTTPException(status_code=403, detail="can_only_delete_own_photos")

    for suffix in ['xl', 'l', 'm', 's']:
        s3 = boto3.client('s3')
        s3.delete_object(
            Bucket=S3_BUCKET,
            Key="/".join([S3_BUCKET_PHOTO_PATH, photo.secret, f"{photo.id}_{suffix}.jpg"])
        )
    s3.delete_object(
        Bucket=S3_BUCKET,
        Key="/".join([S3_BUCKET_ORIGINAL_PATH, f"{photo.id}_o.jpg"])
    )

    photo.albums = []
    db.add(photo)
    db.delete(photo)
    db.commit()

    raise HTTPException(status_code=200, detail="photo_deleted")


@router.put("/{photo_id}/view")
def increase_viewcount(photo_id: str):
    # No-op during peak traffic — re-enable when load stabilizes
    raise HTTPException(status_code=200, detail="success")
