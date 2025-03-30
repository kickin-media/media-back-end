output "photo_bucket_arn" {
  value = aws_s3_bucket.photo_s3_bucket.arn
}

output "photo_bucket_name" {
  value = aws_s3_bucket.photo_s3_bucket.bucket
}

output "distribution_domain_name" {
  value = aws_cloudfront_distribution.photo_cloudfront_distribution.domain_name
}

output "distribution_hosted_zone_id" {
  value = aws_cloudfront_distribution.photo_cloudfront_distribution.hosted_zone_id
}
