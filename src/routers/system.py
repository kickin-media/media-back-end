import os
import json

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from database import get_db
from sqlmodel import Session, select

from models.photo import Photo
from models.album import Album

from variables import PHOTO_PROCESSING_SQS_QUEUE, S3_BUCKET

import boto3

router = APIRouter(
    tags=["system"]
)


@router.get("/status")
async def get_status(db: Session = Depends(get_db)):
    status = {
        'database': None,
        'sqs': None,
        's3': None,
    }

    # database check
    try:
        photo = db.exec(select(Photo)).first()
        if photo is not None:
            status['database'] = True
        else:
            status['database'] = False
    except Exception as err:
        status['database'] = False

    # amazon sqs check
    try:
        sqs = boto3.client('sqs')
        response = sqs.get_queue_attributes(
            QueueUrl=PHOTO_PROCESSING_SQS_QUEUE,
            AttributeNames=['All']
        )
        if 'QueueArn' in response['Attributes']:
            status['sqs'] = True
        else:
            status['sqs'] = False
    except Exception as err:
        status['sqs'] = False

    # amazon s3 check
    try:
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(S3_BUCKET)
        if bucket.name == S3_BUCKET:
            status['s3'] = True
        else:
            status['s3'] = False
    except Exception as err:
        status['s3'] = False

    return JSONResponse(status_code=(200 if all(status.values()) else 500), content=status)


@router.get("/metrics_app")
async def get_app_metrics(db: Session = Depends(get_db)):
    class PrometheusMetrics:
        def __init__(self, environment):
            self._metrics = {}
            self._environment = environment

        def create_metric(self, name: str, type: str, help: str):
            if name in self._metrics.keys():
                raise Exception(f"Metric {name} already exists.")
            self._metrics[name] = {
                'type': type,
                'help': help,
                'values': []
            }

        def put_metric(self, name: str, labels: {}, value):
            if name not in self._metrics.keys():
                raise Exception(f"Metric {name} is not yet created.")
            self._metrics[name]['values'].append({
                'labels': labels,
                'value': value
            })

        def print_metrics(self):
            response = ""
            for m in self._metrics.keys():
                metric = self._metrics[m]
                response += f"# HELP {m} {metric['help']}\n# TYPE {m} {metric['type']}\n"
                for value in metric['values']:
                    label_texts = [f"environment=\"{self._environment}\""]
                    for l in value['labels'].keys():
                        label_texts.append(f"{l}=\"{value['labels'][l]}\"")
                    labels = ",".join(label_texts)
                    response += f"{m}{{{labels}}} {value['value']}\n"
            return response

    metrics = PrometheusMetrics(environment=os.getenv('ENVIRONMENT'))

    # photo metrics
    metrics.create_metric(name='media_photos_total', type='counter',
                          help='The total number of photos available in the tool.')
    no_photos = db.query(Photo).count()
    metrics.put_metric(name='media_photos_total', value=no_photos, labels={})

    metrics.create_metric(name='media_photos_unprocessed', type='counter',
                          help='The total number of unprocessed photos in the tool.')
    unprocessed_photos = db.query(Photo).filter(Photo.upload_processed is False).count()
    metrics.put_metric(name='media_photos_unprocessed', value=unprocessed_photos, labels={})

    return Response(status_code=200, content=metrics.print_metrics())
