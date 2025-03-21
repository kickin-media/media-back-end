variable "account_id" {
  description = "AWS Account ID"
  default     = "990658861879"
  type        = string
}

variable "stages" {
  description = "The stages this application has"
  type        = map
  default     = {
    "dev" : {
      "name" : "dev",
      "base_domain" : "dev.kick-in.media",
      "extra_cors_hostnames" : ["http://localhost", "http://localhost:3000"]
      "photo_bucket_name" : "kickin-media-photo-dev"
      "certificate_arn" : "arn:aws:acm:us-east-1:990658861879:certificate/85a04c7d-efec-4f18-ad2c-f16f9edb27de"
    },
    "prod" : {
      "name" : "prod",
      "base_domain" : "kick-in.media",
      "extra_cors_hostnames" : []
      "photo_bucket_name" : "kickin-media-photo-prod"
      "certificate_arn" : "arn:aws:acm:us-east-1:990658861879:certificate/9000e290-e8b6-448c-a1e6-6da09a58ee2b"
    }
  }
}