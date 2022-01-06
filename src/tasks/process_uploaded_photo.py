from database import db_session
from sqlmodel import select

from variables import S3_BUCKET, S3_UPLOAD_EXPIRY, \
    S3_BUCKET_UPLOAD_PATH, S3_BUCKET_ORIGINAL_PATH, S3_BUCKET_PHOTO_PATH

from PIL import Image, ExifTags, ImageDraw, ImageFont

from models.photo import Photo

import boto3
import io
import json
from datetime import datetime, timedelta


def task():
    print("Starting processing.")
    with db_session:

        offset = 0

        while True:
            photo = db_session.exec(select(Photo).where(Photo.upload_processed == False).offset(offset)).first()

            if photo is None:
                print("There are no photos to process.")
                break

            try:
                process_photo(db_photo=photo)
            except Exception as err:
                if 'An error occurred (404) when calling the HeadObject operation: Not Found' in str(err):
                    upload_cutoff = datetime.utcnow() - timedelta(seconds=S3_UPLOAD_EXPIRY * 2)
                    if photo.uploaded_at < upload_cutoff:
                        print("Photo {} has not been uploaded and upload window expired. Removing.".format(photo.id))
                        db_session.delete(photo)
                        db_session.commit()
                    else:
                        print("Photo {} has not been uploaded yet. Awaiting upload.".format(photo.id))
                        offset += 1
                else:
                    raise err

        print("Finished processing.")


# async def process_photo_async(photo_data: Photo, db: SessionLocal):
#     yield process_photo(photo_data=photo_data, db=db)


def process_photo(db_photo: Photo):
    with db_session:

        if db_photo.upload_processed:
            re_process = True
            print("Re-processing upload {}...".format(db_photo.id))
        else:
            re_process = False
            print("Processing upload {}...".format(db_photo.id))

        s3 = boto3.resource('s3')

        if re_process:
            upload_location = "/".join([S3_BUCKET_ORIGINAL_PATH, "{}_o.jpg".format(db_photo.id)])
        else:
            upload_location = "/".join([S3_BUCKET_UPLOAD_PATH, db_photo.secret, "{}.jpg".format(db_photo.id)])

        sizes = {
            'original': {
                'path': '{prefix}/{photo_uid}_o.jpg'.format(photo_uid=db_photo.id, prefix=S3_BUCKET_ORIGINAL_PATH)
            },
            'original_size': {
                'path': '{prefix}/{secret}/{photo_uid}_xl.jpg'.format(photo_uid=db_photo.id, secret=db_photo.secret,
                                                                      prefix=S3_BUCKET_PHOTO_PATH)
            },
            'large': {
                'path': '{prefix}/{secret}/{photo_uid}_l.jpg'.format(photo_uid=db_photo.id, secret=db_photo.secret,
                                                                     prefix=S3_BUCKET_PHOTO_PATH),
                'length': 2048
            },
            'medium': {
                'path': '{prefix}/{secret}/{photo_uid}_m.jpg'.format(photo_uid=db_photo.id, secret=db_photo.secret,
                                                                     prefix=S3_BUCKET_PHOTO_PATH),
                'length': 800
            },
            'small': {
                'path': '{prefix}/{secret}/{photo_uid}_s.jpg'.format(photo_uid=db_photo.id, secret=db_photo.secret,
                                                                     prefix=S3_BUCKET_PHOTO_PATH),
                'length': 400
            }
        }

        # Download photo from S3.
        photo_object = s3.Object(S3_BUCKET, upload_location)
        photo_stream = io.BytesIO()
        photo_object.download_fileobj(photo_stream)

        original_image = Image.open(photo_stream)

        # Extract EXIF data.
        image_exif_data = original_image.getexif()
        original_exif_data = original_image.info['exif']

        if image_exif_data is not None:
            new_image_exif = {}
            for k, v in image_exif_data.items():
                if type(v) not in [str, int]:
                    continue
                elif k in ExifTags.TAGS:
                    new_image_exif[ExifTags.TAGS[k]] = v
                else:
                    new_image_exif[k] = v
        else:
            new_image_exif = None

        image = original_image.copy()

        watermarks_dx = image.size[0] // 25
        watermarks_dy = image.size[1] // 25

        # Create watermarked image.
        try:
            watermark = Image.open("./config/watermark.png")
            watermark = watermark.convert("RGBA")
            image = image.convert("RGBA")

            watermark.thumbnail((image.size[0] // 5, image.size[1] // 5))
            watermark_logo_x = int(image.size[0] - watermarks_dx - watermark.size[0])
            watermark_logo_y = int(image.size[1] - watermarks_dy - watermark.size[1])
            image.paste(watermark, (watermark_logo_x, watermark_logo_y), watermark)
            image = image.convert("RGB")
        except OSError:
            pass

        # Add photographer name.
        if db_photo.author is not None:
            image_author_name = ImageDraw.Draw(image)
            font_size = int(image.size[1] // 50)
            watermark_text_x = int(watermarks_dx)
            watermark_text_y = int(image.size[1] - watermarks_dy - font_size)
            try:
                image_author_name_font = ImageFont.truetype("./config/watermark.ttf", font_size)
            except OSError:
                image_author_name_font = ImageFont.truetype("./assets/watermark_default.ttf", font_size)
            image_author_name.text((watermark_text_x, watermark_text_y),
                                   "© {}".format(db_photo.author.name),
                                   (255, 255, 255), font=image_author_name_font)

        # Upload various sizes.
        for size in sizes.keys():
            print("Generating size {}".format(size))
            s3 = boto3.client('s3')
            upload_bytes = io.BytesIO()
            if size == 'original':
                if re_process:
                    print("Skipping re-processing of original.")
                    continue
                original_image.save(upload_bytes, 'JPEG', exif=original_exif_data, quality=100)
            elif size == 'original_size':
                image.save(upload_bytes, 'JPEG', exif=original_exif_data, quality=95)
            else:
                resized_image = image.copy()
                max_size = sizes[size]['length']
                resized_image.thumbnail((max_size, max_size))
                resized_image.save(upload_bytes, 'JPEG', exif=original_exif_data)
            print("Uploading size {}".format(size))
            upload_bytes.seek(0)
            s3.put_object(Body=upload_bytes, Bucket=S3_BUCKET, Key=sizes[size]['path'])

        # Mark as processed.
        db_photo.upload_processed = True
        db_photo.exif_data = json.dumps(new_image_exif)
        db_session.add(db_photo)
        db_session.commit()

        # Remove upload.
        if not re_process:
            s3.delete_object(Bucket=S3_BUCKET, Key=upload_location)

        return True
