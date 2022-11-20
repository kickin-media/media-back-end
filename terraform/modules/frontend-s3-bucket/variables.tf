variable "frontend_bucket_name" {
  description = "Name for the bucket."
  type        = string
}

variable "frontend_bucket_hostnames" {
  description = "The hostnames the bucket will be reachable on."
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