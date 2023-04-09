import botocore.exceptions

from PIL import Image, ImageDraw, ImageFont
from exif import Image as ExifImage

import boto3
import io
import json
import requests


def process(event, context):
    for record in event['Records']:
        process_message = json.loads(record["body"])

        try:
            photo_data = {
                'id': process_message['photo_id'],
                'secret': process_message['photo_secret'],
                'author': process_message['author'],
                'update_secret': process_message['exif_update_secret'],
                'delete_upload': process_message['delete_upload']
            }
            process_metadata = process_message['data']
        except Exception as err:
            raise Exception(f"Message could not be evaluated: {record['body']}")

        print(f"Processing upload {photo_data['id']}...")

        s3 = boto3.resource('s3')

        source_location = process_metadata['S3_SOURCE_PATH']

        sizes = {
            'original': {
                'path': '{prefix}/{photo_uid}_o.jpg'.format(photo_uid=photo_data['id'],
                                                            prefix=process_metadata['S3_BUCKET_ORIGINAL_PATH'])
            },
            'original_size': {
                'path': '{prefix}/{secret}/{photo_uid}_xl.jpg'.format(photo_uid=photo_data['id'],
                                                                      secret=photo_data['secret'],
                                                                      prefix=process_metadata['S3_BUCKET_PHOTO_PATH'])
            },
            'large': {
                'path': '{prefix}/{secret}/{photo_uid}_l.jpg'.format(photo_uid=photo_data['id'],
                                                                     secret=photo_data['secret'],
                                                                     prefix=process_metadata['S3_BUCKET_PHOTO_PATH']),
                'length': 2048
            },
            'medium': {
                'path': '{prefix}/{secret}/{photo_uid}_m.jpg'.format(photo_uid=photo_data['id'],
                                                                     secret=photo_data['secret'],
                                                                     prefix=process_metadata['S3_BUCKET_PHOTO_PATH']),
                'length': 800
            },
            'small': {
                'path': '{prefix}/{secret}/{photo_uid}_s.jpg'.format(photo_uid=photo_data['id'],
                                                                     secret=photo_data['secret'],
                                                                     prefix=process_metadata['S3_BUCKET_PHOTO_PATH']),
                'length': 400
            }
        }

        # Figure out event ID for watermark.
        photo_event_data = requests.get("/".join([process_metadata['API_BASE'], 'photo', photo_data['id'], 'event']))
        photo_event_data = json.loads(photo_event_data.content)
        if 'detail' in photo_event_data.keys():
            if photo_event_data['detail'] == 'photo_not_in_album':
                raise Exception("Upload not yet assigned to album.")
            else:
                raise Exception("Could not determine photo event link.")
        else:
            photo_event_id = photo_event_data['id']

        # Download photo from S3.
        print("Downloading original.")
        try:
            photo_object = s3.Object(process_metadata['S3_BUCKET'], source_location)
            photo_stream = io.BytesIO()
            photo_object.download_fileobj(photo_stream)
        except botocore.exceptions.ClientError as err:
            if 'Not Found' in str(err):
                raise Exception("Upload not yet found.")
            else:
                raise err
        original_image = Image.open(photo_stream)
        print(f"Download completed ({round(photo_object.content_length / (1024 ** 2), 1)} MB).")

        # Extract EXIF data.
        print("Extracting EXIF data.")
        photo_stream.seek(0)
        exif_data = {}
        try:
            exif_object = ExifImage(photo_stream)
        except Exception as err:
            print("Cannot read EXIF from photo {photo}.".format(
                photo=photo_data['id']
            ))
            exif_object = None

        if exif_object is not None:
            for k in exif_object.list_all():
                if k == 'flash':
                    flash_dict = {}
                    for flash_k in dir(exif_object.flash):
                        if not flash_k.startswith('_'):
                            flash_v = getattr(exif_object.flash, flash_k)
                            if type(flash_v) in [str, bool] or str(type(flash_v)).startswith('<enum'):
                                flash_dict[flash_k] = str(flash_v) if type(flash_v) not in [str, bool] else flash_v
                    exif_data['flash'] = flash_dict
                else:
                    try:
                        v = getattr(exif_object, k)
                        exif_data[k] = str(v) if type(v) not in [str, bool] else v
                    except Exception as err:
                        print("Cannot read EXIF property {prop} from photo {photo}.".format(
                            prop=k,
                            photo=photo_data['id']
                        ))

        original_exif_data = None
        if 'exif' not in original_image.info:
            print(f"Image {photo_data['id']} does not have EXIF data.")
        else:
            original_exif_data = original_image.info['exif']
        print("Done.")

        # Process Image
        image = original_image.copy()

        watermarks_dx = image.size[0] // 25
        watermarks_dy = image.size[1] // 25

        print("Downloading watermark.")
        try:
            watermark_object = s3.Object(process_metadata['S3_BUCKET'], f"assets/watermark-{photo_event_id}.png")
            watermark_stream = io.BytesIO()
            watermark_object.download_fileobj(watermark_stream)
            watermark_image = Image.open(watermark_stream)
        except botocore.exceptions.ClientError as err:
            if 'Not Found' in str(err) or 'Forbidden' in str(err):
                print("Event specific watermark not found. Try default one.")
                watermark_image = None
            else:
                raise err

        if watermark_image is None:
            print("Downloading default watermark.")
            try:
                watermark_object = s3.Object(process_metadata['S3_BUCKET'], f"assets/watermark-default.png")
                watermark_stream = io.BytesIO()
                watermark_object.download_fileobj(watermark_stream)
                watermark_image = Image.open(watermark_stream)
            except botocore.exceptions.ClientError as err:
                if 'Not Found' in str(err):
                    raise Exception("No watermark found. Pushing event back on queue.")
                else:
                    raise err

        print("Creating thumbnails.")
        # Create watermarked image.
        try:
            watermark = watermark_image
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
        if photo_data['author'] is not None and len(photo_data['author']) > 0:
            print("Adding watermark text.")
            image_author_name = ImageDraw.Draw(image)
            font_size = int(image.size[1] // 50)

            watermark_text_x = int(watermarks_dx)
            watermark_text_y = int(image.size[1] - watermarks_dy - font_size)

            image_author_name_font = ImageFont.truetype("./watermark-font.ttf", font_size)

            image_author_name.text((watermark_text_x, watermark_text_y),
                                   "© {}".format(photo_data['author']),
                                   (255, 255, 255), font=image_author_name_font)
        else:
            print("No photographer name, not adding text.")

        # Upload various sizes.
        for size in sizes.keys():
            print("Generating size {}".format(size))
            s3 = boto3.client('s3')
            upload_bytes = io.BytesIO()
            if size == 'original':
                if photo_data['delete_upload'] is False:
                    print("Skipping re-processing of original.")
                    continue
                if original_exif_data is not None:
                    original_image.save(upload_bytes, 'JPEG', exif=original_exif_data, quality=100)
                else:
                    original_image.save(upload_bytes, 'JPEG', quality=100)
            elif size == 'original_size':
                if original_exif_data is not None:
                    image.save(upload_bytes, 'JPEG', exif=original_exif_data, quality=95)
                else:
                    image.save(upload_bytes, 'JPEG', quality=95)
            else:
                resized_image = image.copy()
                max_size = sizes[size]['length']
                resized_image.thumbnail((max_size, max_size))
                if original_exif_data is not None:
                    resized_image.save(upload_bytes, 'JPEG', exif=original_exif_data)
                else:
                    resized_image.save(upload_bytes, 'JPEG')
            print("Uploading size {}".format(size))
            upload_bytes.seek(0)
            s3.put_object(Body=upload_bytes, Bucket=process_metadata['S3_BUCKET'], Key=sizes[size]['path'],
                          ContentType='image/jpeg')

        # Mark as processed.
        callback = requests.post(
            url="/".join(
                [process_metadata['API_BASE'], 'photo', photo_data['id'], 'exif', photo_data['update_secret']]),
            json={
                'exif_data': exif_data
            }
        )
        callback_data = json.loads(callback.content)

        if callback.status_code != 200:
            raise Exception("Could not notify API of processing.")

        # Remove upload.
        if photo_data['delete_upload']:
            print("Removing original.")
            s3.delete_object(Bucket=process_metadata['S3_BUCKET'], Key=source_location)
        else:
            print("Leaving original in place.")

        print("Done!")


if __name__ == "__main__":
    with open("./test_source.json") as test_event:
        test_event_data = json.loads(test_event.read())
        process(test_event_data, None)
