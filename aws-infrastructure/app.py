#!/usr/bin/env python3
import aws_cdk as cdk

from components.photo_s3_bucket import S3PhotoBucket
from components.frontend_s3_bucket import S3FrontendBucket
from components.photo_handler import S3PhotoHandler
from components.dns_zone import MediaDNSZone
from components.mysql_backup_bucket import S3BackupBucket

MEDIA_ACCOUNT_ID = "990658861879"
MEDIA_ACCOUNT_REGION = "eu-west-1"
MEDIA_CERTIFICATE_ARN = {
    "prod": "arn:aws:acm:us-east-1:990658861879:certificate/9000e290-e8b6-448c-a1e6-6da09a58ee2b",
    "dev": "arn:aws:acm:us-east-1:990658861879:certificate/85a04c7d-efec-4f18-ad2c-f16f9edb27de"
}

MEDIA_DNS_NAME = "kick-in.media"

app = cdk.App()

stages = ['dev', 'prod']

dns_stack = MediaDNSZone(
    app, 'media-hosted-zone', zone_name=MEDIA_DNS_NAME,
    env=cdk.Environment(account=MEDIA_ACCOUNT_ID, region=MEDIA_ACCOUNT_REGION)
)

backup_stack = S3BackupBucket(
    app, 'db-backup-bucket', bucket_name='kickin-media-db-backup',
    env=cdk.Environment(account=MEDIA_ACCOUNT_ID, region=MEDIA_ACCOUNT_REGION)
)

for stage in stages:
    base_domain = MEDIA_DNS_NAME if stage == "prod" else f"{stage}.{MEDIA_DNS_NAME}"

    photo_bucket_name = "kickin-media-photo-{stage}".format(stage=stage)
    photo_bucket_hostnames = [f"photos.{base_domain}"]

    frontend_bucket_name = "kickin-media-frontend-{stage}".format(stage=stage)
    frontend_bucket_hostnames = [base_domain, f"www.{base_domain}"]

    photo_process_stack = S3PhotoHandler(
        app, "photo-handler-{stage}".format(stage=stage),
        stage=stage, photo_bucket_name=photo_bucket_name
    )

    S3PhotoBucket(
        app, 'photo-bucket-{stage}'.format(stage=stage),
        stage=stage,
        bucket_name=photo_bucket_name,
        bucket_hostnames=photo_bucket_hostnames,
        bucket_hostname_acm_arn=MEDIA_CERTIFICATE_ARN[stage],
        hosted_zone=dns_stack.zone,
        frontend_bucket_hostnames=frontend_bucket_hostnames,
        env=cdk.Environment(account=MEDIA_ACCOUNT_ID, region=MEDIA_ACCOUNT_REGION),
        photo_process_queue=photo_process_stack.sqs_queue
    )

    S3FrontendBucket(
        app, 'frontend-bucket-{stage}'.format(stage=stage),
        bucket_name=frontend_bucket_name,
        bucket_hostnames=frontend_bucket_hostnames,
        bucket_hostname_acm_arn=MEDIA_CERTIFICATE_ARN[stage],
        hosted_zone=dns_stack.zone,
        env=cdk.Environment(account=MEDIA_ACCOUNT_ID, region=MEDIA_ACCOUNT_REGION)
    )

app.synth()
