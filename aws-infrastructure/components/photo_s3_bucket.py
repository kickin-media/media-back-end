from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_s3 as s3,
    aws_iam as iam,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    aws_ssm as ssm
)
from constructs import Construct


class S3PhotoBucket(Stack):

    def __init__(self, scope: Construct, construct_id: str, bucket_name: str, bucket_hostnames: [str],
                 bucket_hostname_acm_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # CloudFront ID

        cloudfront_id = cloudfront.OriginAccessIdentity(
            self, "CloudfrontOID",
            comment="CloudFront identity for {bucket_name}".format(bucket_name=bucket_name)
        )

        # S3 Bucket

        photo_bucket = s3.Bucket(
            self, "PhotoBucket",
            bucket_name=bucket_name,
            website_index_document="index.html",
            access_control=s3.BucketAccessControl.PRIVATE,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        # Bucket Cloudfront Proxy

        cloudfront_proxy = cloudfront.Distribution(
            self, "BucketProxy",
            enabled=True,
            enable_ipv6=True,
            comment="Cloudfront proxy for {bucket_name}".format(bucket_name=photo_bucket.bucket_name),
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(bucket=photo_bucket, origin_access_identity=cloudfront_id),
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            domain_names=bucket_hostnames,
            default_root_object="index.html",
            certificate=acm.Certificate.from_certificate_arn(self, 'ImportedCertificate',
                                                             certificate_arn=bucket_hostname_acm_arn)
        )

        ssm.StringParameter(
            self, 'CloudfrontDnsNameOutput',
            string_value=cloudfront_proxy.distribution_domain_name,
            parameter_name='/media/cloudfront-dns-name/{bucket_name}'.format(bucket_name=bucket_name),
            description='The DNS name of the Cloudfront distribution for {bucket_name}.'.format(bucket_name=bucket_name)
        )

        # Bucket Upload User

        upload_user = iam.User(
            self, "UploadUser",
            user_name="{bucket_name}-upload-user".format(bucket_name=photo_bucket.bucket_name)
        )

        upload_user.add_managed_policy(
            policy=iam.ManagedPolicy(
                self, "UploadUserManagedPolicy",
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["s3:PutObject", "s3:GetObject", "s3:HeadObject", "s3:DeleteObject"],
                        resources=["{bucket_arn}/*".format(bucket_arn=photo_bucket.bucket_arn)]
                    ),
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["s3:ListBucket"],
                        resources=["{bucket_arn}".format(bucket_arn=photo_bucket.bucket_arn)]
                    )
                ]
            )
        )

        # S3 Bucket Policies

        photo_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"], effect=iam.Effect.ALLOW,
                resources=[
                    '{bucket_arn}/*'.format(bucket_arn=photo_bucket.bucket_arn)
                ],
                principals=[
                    iam.CanonicalUserPrincipal(cloudfront_id.cloud_front_origin_access_identity_s3_canonical_user_id)
                ]
            )
        )
        photo_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"], effect=iam.Effect.DENY,
                resources=[
                    '{bucket_arn}/originals/*'.format(bucket_arn=photo_bucket.bucket_arn),
                    '{bucket_arn}/uploads/*'.format(bucket_arn=photo_bucket.bucket_arn)
                ],
                principals=[
                    iam.CanonicalUserPrincipal(cloudfront_id.cloud_front_origin_access_identity_s3_canonical_user_id)
                ]
            )
        )
        photo_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket"], effect=iam.Effect.ALLOW,
                resources=[
                    '{bucket_arn}'.format(bucket_arn=photo_bucket.bucket_arn)
                ],
                principals=[
                    iam.CanonicalUserPrincipal(cloudfront_id.cloud_front_origin_access_identity_s3_canonical_user_id)
                ]
            )
        )
