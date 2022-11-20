resource "aws_s3_bucket" "frontend_s3_bucket" {
  bucket = var.frontend_bucket_name
}

resource "aws_s3_bucket_website_configuration" "frontend_s3_bucket_website_configuration" {
  bucket = aws_s3_bucket.frontend_s3_bucket.bucket

  index_document {
    suffix = "index.html"
  }

  routing_rule {
    condition {
      http_error_code_returned_equals = "404"
    }
    redirect {
      host_name               = var.frontend_bucket_hostnames[0]
      replace_key_prefix_with = "#!/"
    }
  }
}

resource "aws_s3_bucket_acl" "frontend_s3_bucket_acl" {
  bucket = aws_s3_bucket.frontend_s3_bucket.bucket
  acl    = "private"
}
resource "aws_s3_bucket_public_access_block" "frontend_s3_bucket_public_acl" {
  bucket                  = aws_s3_bucket.frontend_s3_bucket.bucket
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_policy" "frontend_s3_bucket_policy" {
  bucket = aws_s3_bucket.frontend_s3_bucket.bucket
  policy = data.aws_iam_policy_document.frontend_allow_cloudfront.json
}
data "aws_iam_policy_document" "frontend_allow_cloudfront" {
  statement {
    principals {
      identifiers = [aws_cloudfront_origin_access_identity.frontend_oai.iam_arn]
      type        = "AWS"
    }
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend_s3_bucket.arn}/*"]
  }
  statement {
    principals {
      identifiers = [aws_cloudfront_origin_access_identity.frontend_oai.iam_arn]
      type        = "AWS"
    }
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.frontend_s3_bucket.arn]
  }
}
