from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_iam as iam
)
from constructs import Construct


class S3BackupBucket(Stack):

    def __init__(self, scope: Construct, construct_id: str, bucket_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket
        backup_bucket = s3.Bucket(
            self, "BackupBucket",
            bucket_name=bucket_name,
            access_control=s3.BucketAccessControl.PRIVATE,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    enabled=True,
                    abort_incomplete_multipart_upload_after=Duration.days(1),
                    noncurrent_version_expiration=Duration.days(31)
                )
            ]
        )

        # Bucket Upload User

        backup_user = iam.User(
            self, "DbBackupUser",
            user_name="{bucket_name}-db-backup-user".format(bucket_name=backup_bucket.bucket_name)
        )

        backup_user.add_managed_policy(
            policy=iam.ManagedPolicy(
                self, "BackupUserManagedPolicy",
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["s3:PutObject", "s3:GetObject", "s3:HeadObject"],
                        resources=["{bucket_arn}/*".format(bucket_arn=backup_bucket.bucket_arn)]
                    ),
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["s3:ListBucket"],
                        resources=["{bucket_arn}".format(bucket_arn=backup_bucket.bucket_arn)]
                    )
                ]
            )
        )
