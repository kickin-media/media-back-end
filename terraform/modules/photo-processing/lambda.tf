locals {
  lambda_location = "${path.module}/artifacts/lambda_source.zip"
}

resource "aws_lambda_function" "processing_lambda" {
  function_name = "photo-processing-lambda-${var.stage}"
  role          = aws_iam_role.lambda-execution-role.arn
  handler       = "index.process"
  runtime       = "python3.12"
  memory_size   = 2048
  timeout       = 30

  layers = [
    "arn:aws:lambda:eu-west-1:770693421928:layer:Klayers-p312-Pillow:3"
  ]

  filename         = local.lambda_location
  source_code_hash = data.archive_file.processing_lambda_source.output_base64sha256
}

data "archive_file" "processing_lambda_source" {
  type        = "zip"
  source_dir  = "../lambdas/photo-processing-lambda"
  output_path = local.lambda_location
}

resource "aws_lambda_event_source_mapping" "processing_lambda_event_mapping" {
  function_name    = aws_lambda_function.processing_lambda.arn
  event_source_arn = aws_sqs_queue.photo-processing-queue.arn
  batch_size       = 1
  enabled          = true
}