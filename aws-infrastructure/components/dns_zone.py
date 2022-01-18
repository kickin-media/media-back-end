from aws_cdk import (
    Stack,
    Duration,
    aws_route53 as r53,
    aws_route53_targets as targets,
    aws_ssm as ssm,
    aws_cloudfront as cloudfront
)
from constructs import Construct
import hashlib


class MediaDNSZone(Stack):

    def __init__(self, scope: Construct, construct_id: str, zone_name: str, bucket_aliases: {}, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        zone = r53.HostedZone(self, "Zone", zone_name=zone_name)

        # CAA Record
        r53.CaaRecord(
            self, "CAARecordSet",
            zone=zone,
            record_name=f"{zone_name}.",
            ttl=Duration.minutes(5),
            values=[
                r53.CaaRecordValue(
                    flag=0,
                    tag=r53.CaaTag.IODEF,
                    value="mailto:abuse-caa-kickin-media@jonathanj.nl"
                ),
                r53.CaaRecordValue(
                    flag=0,
                    tag=r53.CaaTag.ISSUE,
                    value="amazonaws.com"
                ),
                r53.CaaRecordValue(
                    flag=0,
                    tag=r53.CaaTag.ISSUEWILD,
                    value="amazonaws.com"
                ),
                r53.CaaRecordValue(
                    flag=0,
                    tag=r53.CaaTag.ISSUE,
                    value="letsencrypt.org"
                ),
                r53.CaaRecordValue(
                    flag=0,
                    tag=r53.CaaTag.ISSUEWILD,
                    value="letsencrypt.org"
                )
            ]
        )

        # ACM Validation
        r53.CnameRecord(
            self, "ACMValidationRecordSet",
            zone=zone,
            record_name=f"_8cade9b0c5c37ed85fb1334e555b09e4.{zone_name}.",
            ttl=Duration.minutes(5),
            domain_name="_120c7ca5fe0a3137f32cdc74922dc008.fsdcfjjflr.acm-validations.aws."
        )

        # Developtment API
        r53.RecordSet(
            self, "DeveloptmentAPIRecordSet",
            zone=zone,
            record_name=f"api.dev.{zone_name}.",
            type=r53.RecordType.CNAME,
            ttl=Duration.minutes(5),
            target=r53.RecordTarget.from_values("nas.jonathanj.nl.")
        )

        # Bucket Aliases
        # DO THIS THE OTHER WAY AROUND TODO??
        for hostname in bucket_aliases.keys():
            r_id = hashlib.md5(hostname).hexdigest()
            target = cloudfront.Distribution.from_distribution_attributes(
                self, f"CloudfrontDist_{r_id}",
                distribution_id="",
                domain_name=""
            )
            r53.ARecord(
                self, f"BucketAliasRecordSet_A_{r_id}",
                zone=zone,
                record_name=f"{hostname}.",
                target=r53.RecordTarget.from_alias(targets.CloudFrontTarget(target))
            )
            r53.AaaaRecord(
                self, f"BucketAliasRecordSet_AAAA_{r_id}",
                zone=zone,
                record_name=f"{hostname}.",
                target=r53.RecordTarget.from_alias(targets.CloudFrontTarget(target))
            )
