variable "account_id" {
  description = "AWS Account ID"
  default     = "934441747922"
  type        = string
}

variable "stages" {
  description = "The stages this application has"
  type        = map
  default     = {
    "prod" : {
      "name" : "prod",
      "base_domain" : "fotos.sterrenkunde.nl",
      "extra_cors_hostnames" : []
      "photo_bucket_name" : "jwg-media-photo-prod"
      "certificate_arn" : "arn:aws:acm:us-east-1:934441747922:certificate/41106d7e-16fc-4704-a68e-f95e347b8400"
      "route53_zone_id" : "Z01850212BY6ZHJFDRWAN"
    }
  }
}