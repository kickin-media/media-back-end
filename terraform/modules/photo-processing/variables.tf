variable "stage" {
  description = "The stage for this processing pipeline."
  type        = string
}

variable "photo_bucket_arn" {
  description = "ARN for the S3 bucket where the processing gets and puts is photos."
  type        = string
}

variable "suppress_author_copyright" {
  description = "Allows for suppressing adding the author copyright watermark to processed photos."
  type        = bool
  default     = false
}