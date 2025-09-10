resource "aws_cloudfront_origin_access_identity" "frontend_oai" {
  comment = "CloudFront identity for ${var.frontend_bucket_name}"
}

resource "aws_cloudfront_distribution" "frontend_cloudfront_distribution" {
  enabled         = true
  is_ipv6_enabled = true

  comment = "Cloudfront proxy for ${var.frontend_bucket_name}"

  viewer_certificate {
    acm_certificate_arn = var.bucket_acm_arn
    ssl_support_method  = "sni-only"
  }
  aliases = var.frontend_bucket_hostnames

  default_root_object = "index.html"
  custom_error_response {
    error_code            = 404
    error_caching_min_ttl = 60
    response_code         = 200
    response_page_path    = "/index.html"
  }

  origin {
    origin_id   = "origin1"
    domain_name = aws_s3_bucket.frontend_s3_bucket.bucket_regional_domain_name
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.frontend_oai.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods = ["GET", "HEAD"]
    target_origin_id       = "origin1"
    compress               = true

    function_association {
      event_type   = "viewer-request"
      function_arn = var.frontend_insecure_auth_password != "" ? aws_cloudfront_function.insecure_basic_auth.arn : aws_cloudfront_function.noop.arn
    }

    # Managed-CachingOptimized / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-managed-cache-policies.html
    cache_policy_id = var.frontend_insecure_auth_password != "" ? aws_cloudfront_cache_policy.vary_on_auth.id : "658327ea-f89d-4fab-a63d-7e88639e58f6"
    # Managed-AllViewerExceptHostHeader / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-managed-origin-request-policies.html
    origin_request_policy_id = var.frontend_insecure_auth_password != "" ? aws_cloudfront_origin_request_policy.no_auth.id : "b689b0a8-53d0-40ab-baf2-68738e2966ac"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

}