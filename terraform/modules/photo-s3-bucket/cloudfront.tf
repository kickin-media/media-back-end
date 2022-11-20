resource "aws_cloudfront_origin_access_identity" "photo_oai" {
  comment = "CloudFront identity for ${var.photo_bucket_name}"
}

resource "aws_cloudfront_distribution" "photo_cloudfront_distribution" {
  enabled         = true
  is_ipv6_enabled = true

  comment = "Cloudfront proxy for ${var.photo_bucket_name}"

  viewer_certificate {
    acm_certificate_arn = var.bucket_acm_arn
    ssl_support_method  = "sni-only"
  }
  aliases = var.photo_bucket_hostnames

  origin {
    origin_id   = "origin1"
    domain_name = aws_s3_bucket.photo_s3_bucket.bucket_regional_domain_name
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.photo_oai.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "origin1"
    compress               = true
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    response_headers_policy_id = aws_cloudfront_response_headers_policy.photo_cloudfront_response_headers_policy.id
  }


  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

}

resource "aws_cloudfront_response_headers_policy" "photo_cloudfront_response_headers_policy" {
  name    = "MediaCorsResponseHeadersPolicy-${var.stage}"
  comment = "Policy to ensure CORS headers are always passed on photos, even if they're cached without."

  cors_config {
    access_control_allow_credentials = true
    access_control_max_age_sec       = 600
    origin_override                  = false

    access_control_allow_headers {
      items = ["Authorization"]
    }

    access_control_allow_methods {
      items = ["GET", "POST"]
    }

    access_control_allow_origins {
      items = var.photo_cors_hostnames
    }
  }
}