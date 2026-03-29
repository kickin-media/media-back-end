variable "frontend_bucket_name" {
  description = "Name for the bucket."
  type        = string
}

variable "frontend_bucket_hostnames" {
  description = "The hostnames the bucket will be reachable on."
  type = list(string)
}

variable "bucket_acm_arn" {
  description = "The ACM ARN of the certificate that will be used for TLS on this bucket."
  type        = string
}

variable "frontend_workflow_repo" {
  description = "The GitHub repository in which the workflow lives that publishes the frontend."
  type        = string
  default     = "kickin-media/media-front-end"
}