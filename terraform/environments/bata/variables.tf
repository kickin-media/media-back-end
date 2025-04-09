variable "account_id" {
  description = "AWS Account ID"
  default     = "172483268424"
  type        = string
}

variable "stages" {
  description = "The stages this application has"
  type        = map
  default     = {
    "prod" : {
      "name" : "prod",
      "base_domain" : "fotos.batavierenrace.nl",
      "extra_cors_hostnames" : []
      "photo_bucket_name" : "bata-media-photo-prod"
      "certificate_arn" : "arn:aws:acm:us-east-1:172483268424:certificate/31af764e-4a4e-4586-a7e3-93cce81656ba"
      "route53_zone_id" : "Z0501357TFKZ7NM83UD2"
    }
  }
}