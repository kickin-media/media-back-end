output "certificate_arn" {
  value = aws_acm_certificate.cert.arn
}

output "certificate_id" {
  value = aws_acm_certificate.cert.id
}