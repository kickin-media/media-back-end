output "frontend_hostnames" {
  value = var.frontend_bucket_hostnames
}

output "distribution_domain_name" {
  value = aws_cloudfront_distribution.frontend_cloudfront_distribution.domain_name
}

output "distribution_hosted_zone_id" {
  value = aws_cloudfront_distribution.frontend_cloudfront_distribution.hosted_zone_id
}
