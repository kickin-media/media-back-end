variable "account_id" {
  description = "AWS Account ID"
  default     = "172483268424"
  type        = string
}

variable "stages" {
  description = "The stages this application has"
  type        = map
  default     = {
    "dev" : {
      "name" : "dev",
      "base_domain" : "dev.fotos.batavierenrace.nl",
      "extra_cors_hostnames" : ["http://localhost", "http://localhost:3000"]
      "photo_bucket_name" : "bata-media-photo-dev"
      "certificate_arn" : "arn:aws:acm:us-east-1:xxx:certificate/xxx"
    },
    "prod" : {
      "name" : "prod",
      "base_domain" : "fotos.batavierenrace.nl",
      "extra_cors_hostnames" : []
      "photo_bucket_name" : "bata-media-photo-prod"
      "certificate_arn" : "arn:aws:acm:us-east-1:xxx:certificate/xxx"
    }
  }
}