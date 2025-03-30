# Route53 records for the asset bucket that contains the photo files
resource "aws_route53_record" "photo_bucket_record_a" {
  zone_id = var.route53_zone_id
  name    = var.photo_record_name
  type    = "A"

  alias {
    evaluate_target_health = false
    name                   = var.photo_cloudfront_dns_name
    zone_id                = var.photo_cloudfront_hosted_zone_id
  }
}

resource "aws_route53_record" "photo_bucket_record_aaaa" {
  zone_id = var.route53_zone_id
  name    = var.photo_record_name
  type    = "AAAA"

  alias {
    evaluate_target_health = false
    name                   = var.photo_cloudfront_dns_name
    zone_id                = var.photo_cloudfront_hosted_zone_id
  }
}

# Route53 records for the asset bucket that contains the frontend files
resource "aws_route53_record" "frontend_bucket_record_a" {
  zone_id = var.route53_zone_id
  name    = var.frontend_record_name
  type    = "A"

  alias {
    evaluate_target_health = false
    name                   = var.frontend_cloudfront_dns_name
    zone_id                = var.frontend_cloudfront_hosted_zone_id
  }
}

resource "aws_route53_record" "frontend_bucket_record_aaaa" {
  zone_id = var.route53_zone_id
  name    = var.frontend_record_name
  type    = "AAAA"

  alias {
    evaluate_target_health = false
    name                   = var.frontend_cloudfront_dns_name
    zone_id                = var.frontend_cloudfront_hosted_zone_id
  }
}

resource "aws_route53_record" "frontend_bucket_record_apex_a" {
  count = var.frontend_record_for_apex ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "@"
  type    = "A"

  alias {
    evaluate_target_health = false
    name                   = var.frontend_cloudfront_dns_name
    zone_id                = var.frontend_cloudfront_hosted_zone_id
  }
}

resource "aws_route53_record" "frontend_bucket_record_apex_aaaa" {
  count = var.frontend_record_for_apex ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "@"
  type    = "AAAA"

  alias {
    evaluate_target_health = false
    name                   = var.frontend_cloudfront_dns_name
    zone_id                = var.frontend_cloudfront_hosted_zone_id
  }
}