resource "aws_route53_record" "aws_server_record_ipv4" {
  for_each = toset(var.frontend_bucket_hostnames)

  name    = each.key
  type    = "A"
  zone_id = var.hosted_zone_id

  alias {
    evaluate_target_health = false
    name                   = aws_cloudfront_distribution.frontend_cloudfront_distribution.domain_name
    zone_id                = "Z2FDTNDATAQYW2"
  }
}

resource "aws_route53_record" "aws_server_record_ipv6" {
  for_each = toset(var.frontend_bucket_hostnames)

  name    = each.key
  type    = "AAAA"
  zone_id = var.hosted_zone_id

  alias {
    evaluate_target_health = false
    name                   = aws_cloudfront_distribution.frontend_cloudfront_distribution.domain_name
    zone_id                = "Z2FDTNDATAQYW2"
  }
}
