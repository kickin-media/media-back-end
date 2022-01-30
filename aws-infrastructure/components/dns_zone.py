from aws_cdk import (
    Stack,
    Duration,
    aws_route53 as r53,
)
from constructs import Construct


class MediaDNSZone(Stack):
    zone: r53.HostedZone

    def __init__(self, scope: Construct, construct_id: str, zone_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.zone = r53.HostedZone(self, "Zone", zone_name=zone_name)

        # CAA Record
        r53.CaaRecord(
            self, "CAARecordSet",
            zone=self.zone,
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
            self, "ACMValidationRecordSetProd",
            zone=self.zone,
            record_name=f"_8cade9b0c5c37ed85fb1334e555b09e4.{zone_name}.",
            ttl=Duration.minutes(5),
            domain_name="_120c7ca5fe0a3137f32cdc74922dc008.fsdcfjjflr.acm-validations.aws."
        )
        r53.CnameRecord(
            self, "ACMValidationRecordSetDev",
            zone=self.zone,
            record_name=f"_5900bc4aac5f2875f40f47bf8f651b5a.dev.{zone_name}.",
            ttl=Duration.minutes(5),
            domain_name="_f3ff463096b7c942bd4fae4cc8cf9335.pczglchxlc.acm-validations.aws."
        )

        # Production API
        r53.CnameRecord(
            self, "ProductionAPIRercordSet",
            zone=self.zone,
            record_name=f"api.{zone_name}.",
            ttl=Duration.minutes(5),
            # For the WKI we'll host prod locally as well.
            domain_name="nas.jonathanj.nl."
        )

        # Development API
        r53.CnameRecord(
            self, "DeveloptmentAPIRecordSet",
            zone=self.zone,
            record_name=f"api.dev.{zone_name}.",
            ttl=Duration.minutes(5),
            domain_name="nas.jonathanj.nl."
        )
