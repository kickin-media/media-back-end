module "frontend_bucket" {
  for_each = var.stages
  source   = "../../modules/frontend-s3-bucket"

  frontend_bucket_name = "bata-media-frontend-${each.key}"
  frontend_bucket_hostnames = [
    each.value.base_domain,
    "www.${each.value.base_domain}"
  ]

  bucket_acm_arn = each.value.certificate_arn
}

module "processing_queue" {
  for_each = var.stages
  source   = "../../modules/photo-processing"

  photo_bucket_arn = "arn:aws:s3:::${each.value.photo_bucket_name}"
  stage            = each.key
}

module "photo_bucket" {
  for_each = var.stages
  source   = "../../modules/photo-s3-bucket"

  photo_bucket_name = each.value.photo_bucket_name
  photo_bucket_hostnames = [
    "assets.${each.value.base_domain}",
  ]

  bucket_acm_arn = each.value.certificate_arn

  photo_cors_hostnames = setunion(each.value.extra_cors_hostnames, [
    for hostname in module.frontend_bucket[each.key].frontend_hostnames : "https://${hostname}"
  ])
  sqs_processing_queue_arn = module.processing_queue[each.key].processing_queue_arn
  stage                    = each.key
}

module "route53" {
  for_each = var.stages
  source   = "../../modules/dns"

  route53_zone_id          = each.value.route53_zone_id
  frontend_record_for_apex = true

  frontend_cloudfront_dns_name       = module.frontend_bucket[each.key].distribution_domain_name
  frontend_cloudfront_hosted_zone_id = module.frontend_bucket[each.key].distribution_hosted_zone_id

  photo_cloudfront_dns_name       = module.photo_bucket[each.key].distribution_domain_name
  photo_cloudfront_hosted_zone_id = module.photo_bucket[each.key].distribution_hosted_zone_id
  photo_record_name = "assets"
}