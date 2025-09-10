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

# Simple but insecure authentication.
variable "frontend_insecure_auth_password" {
  description = "A very simple but insecure password that is required to access the front-end. This is not intended to be secure, just to prevent casual access and/or scrapers."
  type        = string
  default     = ""
}

variable "frontend_insecure_auth_user" {
  description = "The user name to access the front-end."
  type        = string
  default     = ""
}

variable "frontend_insecure_auth_prompt" {
  description = "The prompt that is shown when the user is asked to authenticate."
  type        = string
  default     = ""
}