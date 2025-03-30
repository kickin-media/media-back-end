variable "route53_zone_id" {
  description = "Zone ID for an existing Route53 zone to put the new records in."
  type        = string
}

variable "photo_record_name" {
  description = "The name of the record to create for the photo bucket."
  type        = string
  default     = "photos"
}

variable "photo_cloudfront_dns_name" {
  description = "The DNS name of the CloudFront distribution for the photo bucket to use in the alias record."
  type        = string
}

variable "photo_cloudfront_hosted_zone_id" {
  description = "The hosted zone ID of the CloudFront distribution for the photo bucket to use in the alias record."
  type        = string
}

variable "frontend_record_name" {
  description = "The name of the record to create for the frontend bucket."
  type        = string
  default     = "www"
}

variable "frontend_record_for_apex" {
  description = "Whether to create a record for the domain apex as well."
  type        = bool
  default     = true
}

variable "frontend_cloudfront_dns_name" {
  description = "The DNS name of the CloudFront distribution for the frontend bucket to use in the alias record."
  type        = string
}

variable "frontend_cloudfront_hosted_zone_id" {
  description = "The hosted zone ID of the CloudFront distribution for the frontend bucket to use in the alias record."
  type        = string
}