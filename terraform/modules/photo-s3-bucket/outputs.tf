output "photo_bucket_arn" {
  value = aws_s3_bucket.photo_s3_bucket.arn
}

output "photo_bucket_name" {
  value = aws_s3_bucket.photo_s3_bucket.bucket
}