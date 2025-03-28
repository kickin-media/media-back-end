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
      "base_domain" : "dev.foto.batavierenrace.nl",
      "extra_cors_hostnames" : ["http://localhost", "http://localhost:3000"]
      "photo_bucket_name" : "bata-media-photo-dev"
      "certificate_arn" : "arn:aws:acm:us-east-1:172483268424:certificate/c8660770-d8c2-4976-9d95-145289b45c1e"
    },
    "prod" : {
      "name" : "prod",
      "base_domain" : "foto.batavierenrace.nl",
      "extra_cors_hostnames" : []
      "photo_bucket_name" : "bata-media-photo-prod"
      "certificate_arn" : "arn:aws:acm:us-east-1:172483268424:certificate/411d3e09-0a4e-4ed1-b73d-9c7e69d9d2da"
    }
  }
}