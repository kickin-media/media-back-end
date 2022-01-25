from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_iam as iam,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    aws_route53 as r53,
    aws_route53_targets as targets
)
from constructs import Construct


class S3FrontendBucket(Stack):

    def __init__(self, scope: Construct, construct_id: str, bucket_name: str, bucket_hostnames: [str],
                 bucket_hostname_acm_arn: str, hosted_zone: r53.HostedZone, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # CloudFront ID

        cloudfront_id = cloudfront.OriginAccessIdentity(
            self, "CloudfrontOID",
            comment="CloudFront identity for {bucket_name}".format(bucket_name=bucket_name)
        )

        # S3 Bucket

        frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            bucket_name=bucket_name,
            website_index_document="index.html",
            website_routing_rules=[
                s3.RoutingRule(
                    condition=s3.RoutingRuleCondition(
                        http_error_code_returned_equals="404"
                    ),
                    host_name=bucket_hostnames[0],
                    replace_key=s3.ReplaceKey.prefix_with("#!/")
                )
            ],
            access_control=s3.BucketAccessControl.PRIVATE,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        # Bucket Cloudfront Proxy

        cloudfront_proxy = cloudfront.CloudFrontWebDistribution(
            self, "BucketProxy",
            enabled=True,
            enable_ip_v6=True,
            comment="Cloudfront proxy for {bucket_name}".format(bucket_name=frontend_bucket.bucket_name),
            viewer_certificate=cloudfront.ViewerCertificate.from_acm_certificate(
                acm.Certificate.from_certificate_arn(self, 'ImportedCertificate',
                                                     certificate_arn=bucket_hostname_acm_arn),
                aliases=bucket_hostnames),
            default_root_object="index.html",
            error_configurations=[
                cloudfront.CfnDistribution.CustomErrorResponseProperty(
                    error_caching_min_ttl=60,
                    error_code=404,
                    response_code=200,
                    response_page_path="/index.html"
                )
            ],
            origin_configs=[
                cloudfront.SourceConfiguration(
                    behaviors=[cloudfront.Behavior(
                        is_default_behavior=True,
                        viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                        allowed_methods=cloudfront.CloudFrontAllowedMethods.GET_HEAD_OPTIONS
                    )],
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=frontend_bucket,
                        origin_access_identity=cloudfront_id
                    )
                )
            ]
        )

        # Bucket Upload User

        upload_user = iam.User(
            self, "UploadUser",
            user_name="{bucket_name}-upload-user".format(bucket_name=frontend_bucket.bucket_name)
        )

        upload_user.add_managed_policy(
            policy=iam.ManagedPolicy(
                self, "UploadUserManagedPolicy",
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["s3:PutObject", "s3:PutObjectAcl", "s3:GetObject", "s3:HeadObject", "s3:DeleteObject"],
                        resources=["{bucket_arn}/*".format(bucket_arn=frontend_bucket.bucket_arn)]
                    ),
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["s3:ListBucket"],
                        resources=["{bucket_arn}".format(bucket_arn=frontend_bucket.bucket_arn)]
                    )
                ]
            )
        )

        # S3 Bucket Policies

        frontend_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"], effect=iam.Effect.ALLOW,
                resources=[
                    '{bucket_arn}/*'.format(bucket_arn=frontend_bucket.bucket_arn)
                ],
                principals=[
                    iam.CanonicalUserPrincipal(cloudfront_id.cloud_front_origin_access_identity_s3_canonical_user_id)
                ]
            )
        )
        frontend_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket"], effect=iam.Effect.ALLOW,
                resources=[
                    '{bucket_arn}'.format(bucket_arn=frontend_bucket.bucket_arn)
                ],
                principals=[
                    iam.CanonicalUserPrincipal(cloudfront_id.cloud_front_origin_access_identity_s3_canonical_user_id)
                ]
            )
        )

        # DNS

        for hostname in bucket_hostnames:
            for record in [r53.ARecord, r53.AaaaRecord]:
                record(
                    self, "{}{}".format(record.__name__, hostname.replace(".", "-")),
                    zone=hosted_zone,
                    record_name=hostname,
                    ttl=Duration.minutes(5),
                    target=r53.RecordTarget.from_alias(targets.CloudFrontTarget(distribution=cloudfront_proxy))
                )
