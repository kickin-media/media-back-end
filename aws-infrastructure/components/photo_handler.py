from aws_cdk import (
    Stack,
    Duration,
    aws_sqs as sqs,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_events
)
from constructs import Construct
import os


class S3PhotoHandler(Stack):

    def __init__(self, scope: Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # SQS Queue

        self.sqs_queue = sqs.Queue(
            self, "PhotoEventQueue",
            queue_name=f"media-photo-processing-{stage}",
            encryption=sqs.QueueEncryption.KMS_MANAGED,
            retention_period=Duration.days(14)
        )

        # Lambda Execution Role

        execution_role = iam.Role(
            self, "LambdaExectionRole",
            role_name=f"media-photo-processing-{stage}-execution-role",
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            inline_policies=[
                iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                            effect=iam.Effect.ALLOW,
                            resources=["*"]
                        ),
                        iam.PolicyStatement(
                            actions=["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"],
                            effect=iam.Effect.ALLOW,
                            resources=[self.sqs_queue.queue_arn]
                        )
                    ]
                )
            ]
        )

        # Processing Lambda

        processing_lambda = _lambda.Function(
            self, "LambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="index.process",
            code=_lambda.Code.from_asset(os.path.join("components", "photo-processing-lambda"))
        )

        event_source_mapping = lambda_events.SqsEventSource(
            queue=self.sqs_queue,
            batch_size=10,
            enabled=True
        )

        processing_lambda.add_event_source(event_source_mapping)
