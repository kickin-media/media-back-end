variable "account_id" {
  description = "AWS Account ID"
  default     = "990658861879"
  type        = string
}

variable "zone_name" {
  description = "The DNS zone for application deployment."
  default     = "kick-in.media"
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
    },
    "prod" : {
      "name" : "prod",
      "base_domain" : "kick-in.media",
      "extra_cors_hostnames" : []
      "photo_bucket_name" : "kickin-media-photo-prod"
    }
  }
}