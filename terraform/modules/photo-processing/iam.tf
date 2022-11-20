resource "aws_iam_role" "lambda-execution-role" {
  name               = "media-photo-processing-${var.stage}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.lambda-trust-policy.json
}

resource "aws_iam_role_policy_attachment" "lambda-execution-role-policy" {
  role       = aws_iam_role.lambda-execution-role.id
  policy_arn = aws_iam_policy.lambda-role-policy.arn
}

resource "aws_iam_policy" "lambda-role-policy" {
  policy = data.aws_iam_policy_document.lambda-role-policy-document.json
  name   = "media-photo-processing-${var.stage}-processing-policy"
}

data "aws_iam_policy_document" "lambda-role-policy-document" {
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    effect    = "Allow"
    resources = ["*"]
  }
  statement {
    actions   = [
      "sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes", "sqs:GetQueueUrl",
      "sqs:ChangeMessageVisibility"
    ]
    effect    = "Allow"
    resources = [aws_sqs_queue.photo-processing-queue.arn]
  }
  statement {
    actions   = ["s3:PutObject", "s3:GetObject", "s3:HeadObject", "s3:DeleteObject"]
    effect    = "Allow"
    resources = ["${var.photo_bucket_arn}/*"]
  }
}

data "aws_iam_policy_document" "lambda-trust-policy" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}