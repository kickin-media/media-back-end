# CAA Records
resource "aws_route53_record" "media_caa_record" {
  name    = "${aws_route53_zone.media_zone.name}."
  type    = "CAA"
  zone_id = aws_route53_zone.media_zone.id
  ttl     = 3600
  records = [
    "0 iodef \"mailto:abuse-caa-kickin-media@jonathanj.nl\"",
    "0 issuewild \"letsencrypt.org\"",
    "0 issuewild \"amazonaws.com\"",
    "0 issue \"amazonaws.com\"",
    "0 issue \"letsencrypt.org\""
  ]
}

# API Server Records
resource "aws_route53_record" "aws_server_record" {
  name    = "aws.${aws_route53_zone.media_zone.name}"
  type    = "A"
  zone_id = aws_route53_zone.media_zone.id
  ttl     = 300
  records = [
    "34.244.161.121"
  ]
}
resource "aws_route53_record" "aws_server_record_wildcard" {
  name    = "*.aws.${aws_route53_zone.media_zone.name}"
  type    = "A"
  zone_id = aws_route53_zone.media_zone.id
  ttl     = 300
  records = [
    "34.244.161.121"
  ]
}

resource "aws_route53_record" "aws_api_prod_record" {
  name    = "api.${aws_route53_zone.media_zone.name}"
  type    = "CNAME"
  zone_id = aws_route53_zone.media_zone.id
  ttl     = 300
  records = [
    "${aws_route53_record.aws_server_record.name}."
  ]
}
resource "aws_route53_record" "aws_api_dev_record" {
  name    = "api.dev.${aws_route53_zone.media_zone.name}"
  type    = "CNAME"
  zone_id = aws_route53_zone.media_zone.id
  ttl     = 300
  records = [
    "${aws_route53_record.aws_server_record.name}."
  ]
}

# E-mail Records
resource "aws_route53_record" "media_mail_mx_record" {
  name    = "${aws_route53_zone.media_zone.name}."
  type    = "MX"
  zone_id = aws_route53_zone.media_zone.id
  ttl     = 3600
  records = [
    "20 in2-smtp.messagingengine.com",
    "10 in1-smtp.messagingengine.com"
  ]
}
resource "aws_route53_record" "media_mail_spf_record" {
  name    = "${aws_route53_zone.media_zone.name}."
  type    = "TXT"
  zone_id = aws_route53_zone.media_zone.id
  ttl     = 3600
  records = [
    "v=spf1 include:spf.messagingengine.com ?all"
  ]
}
resource "aws_route53_record" "media_mail_dkim_record" {
  for_each = toset(["1", "2", "3"])

  name    = "fm${each.key}._domainkey.${aws_route53_zone.media_zone.name}."
  type    = "CNAME"
  zone_id = aws_route53_zone.media_zone.id
  ttl     = 3600
  records = [
    "fm${each.key}.kick-in.media.dkim.fmhosted.com"
  ]
}
