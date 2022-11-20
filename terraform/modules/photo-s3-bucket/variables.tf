variable "photo_bucket_name" {
  description = "Name for the bucket."
  type        = string
}

variable "photo_bucket_hostnames" {
  description = "The hostnames the bucket will be reachable on."
  type        = list(string)
}

variable "photo_cors_hostnames" {
  description = "Additional CORS hostnames."
  type        = list(string)
}

variable "bucket_acm_arn" {
  description = "The ACM ARN of the certificate that will be used for TLS on this bucket."
  type        = string
}

variable "hosted_zone_id" {
  description = "Hosted Zone to make the CloudFront records in."
  type        = string
}

variable "stage" {
  description = "Stage name."
  type        = string
}

variable "sqs_processing_queue_arn" {
  description = "The ARN of an SQS queue used for photo processing."
  type        = string
}