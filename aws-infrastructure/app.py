#!/usr/bin/env python3
import aws_cdk as cdk

from components.photo_s3_bucket import S3PhotoBucket
from components.frontend_s3_bucket import S3FrontendBucket
from components.dns_zone import MediaDNSZone

MEDIA_ACCOUNT_ID = "990658861879"
MEDIA_ACCOUNT_REGION = "eu-west-1"
MEDIA_CERTIFICATE_ARN = "arn:aws:acm:us-east-1:990658861879:certificate/9000e290-e8b6-448c-a1e6-6da09a58ee2b"

MEDIA_DNS_NAME = "kick-in.media"

app = cdk.App()

stages = ['dev', 'prod']
bucket_aliases = {}

for stage in stages:
    photo_bucket_name = "kickin-media-photo-{stage}".format(stage=stage)
    photo_bucket_hostnames = [
        ("photos.{apex}" if stage == "prod" else "photos.{stage}.{apex}").format(apex=MEDIA_DNS_NAME, stage=stage)
    ]
    S3PhotoBucket(
        app, 'photo-bucket-{stage}'.format(stage=stage),
        bucket_name=photo_bucket_name,
        bucket_hostnames=photo_bucket_hostnames,
        bucket_hostname_acm_arn=MEDIA_CERTIFICATE_ARN,
        env=cdk.Environment(account=MEDIA_ACCOUNT_ID, region=MEDIA_ACCOUNT_REGION)
    )
    for h in photo_bucket_hostnames:
        bucket_aliases[h] = photo_bucket_name

    frontend_bucket_name = "kickin-media-frontend-{stage}".format(stage=stage)
    frontend_bucket_hostnames = [
        ("{apex}" if stage == "prod" else "{stage}.{apex}").format(apex=MEDIA_DNS_NAME, stage=stage),
        ("www.{apex}" if stage == "prod" else "www.{stage}.{apex}").format(apex=MEDIA_DNS_NAME, stage=stage)
    ]
    S3FrontendBucket(
        app, 'frontend-bucket-{stage}'.format(stage=stage),
        bucket_name=frontend_bucket_name,
        bucket_hostnames=frontend_bucket_hostnames,
        bucket_hostname_acm_arn=MEDIA_CERTIFICATE_ARN,
        env=cdk.Environment(account=MEDIA_ACCOUNT_ID, region=MEDIA_ACCOUNT_REGION)
    )
    for h in frontend_bucket_hostnames:
        bucket_aliases[h] = frontend_bucket_hostnames

MediaDNSZone(app, 'media-hosted-zone', zone_name=MEDIA_DNS_NAME, bucket_aliases=bucket_aliases)

app.synth()
