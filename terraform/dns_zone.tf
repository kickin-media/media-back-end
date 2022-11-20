resource "aws_route53_zone" "media_zone" {
  name = "kick-in.media"
}

module "media_zone_certificate" {
  for_each = var.stages

  source = "./modules/acm_certificate"

  providers = {
    aws.region = aws
    aws.global = aws.aws-global
  }

  domain_name               = each.value.base_domain
  hosted_zone_id            = aws_route53_zone.media_zone.zone_id
  subject_alternative_names = [
    "*.${each.value.base_domain}"
  ]
}