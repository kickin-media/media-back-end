resource "aws_sqs_queue" "photo-processing-queue" {
  name                      = "media-photo-processing-${var.stage}"
  sqs_managed_sse_enabled   = true
  message_retention_seconds = 14*24*3600

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.photo-processing-queue-dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_sqs_queue" "photo-processing-queue-dlq" {
  name                      = "media-photo-processing-${var.stage}-dlq"
  sqs_managed_sse_enabled   = true
  message_retention_seconds = 14*24*3600
}