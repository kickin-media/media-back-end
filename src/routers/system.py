from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from database import get_db
from sqlmodel import Session, select

from models.photo import Photo

from variables import PHOTO_PROCESSING_SQS_QUEUE, S3_BUCKET

import boto3

router = APIRouter(
    tags=["system"]
)


@router.get("/status")
async def get_status(db: Session = Depends(get_db)):
    status = {
        'status': {
            'database': None,
            'sqs': None,
            's3': None,
        },
        'metrics': {
            'photos': {
                'uploads': None,
                'unprocessed': None
            }
        }
    }

    # database check
    try:
        photo = db.exec(select(Photo)).first()
        if photo is not None:
            status['status']['database'] = True
        else:
            status['status']['database'] = False
    except Exception as err:
        status['status']['database'] = False

    # amazon sqs check
    try:
        sqs = boto3.client('sqs')
        response = sqs.get_queue_attributes(
            QueueUrl=PHOTO_PROCESSING_SQS_QUEUE,
            AttributeNames=['All']
        )
        if 'QueueArn' in response['Attributes']:
            status['status']['sqs'] = True
        else:
            status['status']['sqs'] = False
    except Exception as err:
        status['status']['sqs'] = False

    # amazon s3 check
    try:
        s3 = boto3.client('s3')
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            MaxKeys=10
        )
        if len(response['Contents']) > 0:
            status['status']['s3'] = True
        else:
            status['status']['s3'] = False
    except Exception as err:
        status['status']['s3'] = False

    # photo metrics
    no_photos = db.query(Photo).count()
    status['metrics']['photos']['uploads'] = no_photos

    unprocessed_photos = db.query(Photo).filter(Photo.upload_processed is False).count()
    status['metrics']['photos']['unprocessed'] = unprocessed_photos

    return JSONResponse(status_code=(200 if all(status['status'].values()) else 500), content=status)
