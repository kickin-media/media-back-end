module "frontend_bucket" {
  for_each = var.stages
  source   = "./modules/frontend-s3-bucket"

  frontend_bucket_name      = "kickin-media-frontend-${each.key}"
  frontend_bucket_hostnames = [
    each.value.base_domain,
    "www.${each.value.base_domain}"
  ]

  bucket_acm_arn = module.media_zone_certificate[each.key].certificate_arn
  hosted_zone_id = aws_route53_zone.media_zone.zone_id
}

module "processing_queue" {
  for_each = var.stages
  source   = "./modules/photo-processing"

  pillow_layer_arn = data.klayers_package_latest_version.pillow.arn

  photo_bucket_arn = "arn:aws:s3:::${each.value.photo_bucket_name}"
  stage            = each.key
}

module "photo_bucket" {
  for_each = var.stages
  source   = "./modules/photo-s3-bucket"

  photo_bucket_name      = each.value.photo_bucket_name
  photo_bucket_hostnames = [
    "photos.${each.value.base_domain}",
  ]

  bucket_acm_arn = module.media_zone_certificate[each.key].certificate_arn
  hosted_zone_id = aws_route53_zone.media_zone.zone_id

  photo_cors_hostnames = setunion(each.value.extra_cors_hostnames, [
  for hostname in module.frontend_bucket[each.key].frontend_hostnames : "https://${hostname}"
  ])
  sqs_processing_queue_arn = module.processing_queue[each.key].processing_queue_arn
  stage                    = each.key
}

