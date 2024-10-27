resource "aws_s3_bucket" "photo_s3_bucket" {
  bucket = var.photo_bucket_name

}

resource "aws_s3_bucket_cors_configuration" "photo_s3_bucket_cors" {
  bucket = aws_s3_bucket.photo_s3_bucket.bucket
  cors_rule {
    allowed_methods = ["POST", "GET"]
    allowed_origins = var.photo_cors_hostnames
  }
}

resource "aws_s3_bucket_website_configuration" "photo_s3_bucket_website_configuration" {
  bucket = aws_s3_bucket.photo_s3_bucket.bucket

  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "photo_s3_bucket_lifecycle" {
  bucket = aws_s3_bucket.photo_s3_bucket.bucket
  rule {
    id     = "photo-lifecycle-rule"
    status = "Enabled"
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
    noncurrent_version_expiration {
      noncurrent_days = 31
    }
  }
}

resource "aws_s3_bucket_public_access_block" "photo_s3_bucket_public_acl" {
  bucket                  = aws_s3_bucket.photo_s3_bucket.bucket
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_policy" "photo_s3_bucket_policy" {
  bucket = aws_s3_bucket.photo_s3_bucket.bucket
  policy = data.aws_iam_policy_document.photo_allow_cloudfront.json
}
data "aws_iam_policy_document" "photo_allow_cloudfront" {
  statement {
    principals {
      identifiers = [aws_cloudfront_origin_access_identity.photo_oai.iam_arn]
      type        = "AWS"
    }
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.photo_s3_bucket.arn}/*"]
  }
  statement {
    effect = "Deny"
    principals {
      identifiers = [aws_cloudfront_origin_access_identity.photo_oai.iam_arn]
      type        = "AWS"
    }
    actions   = ["s3:GetObject"]
    resources = [
      "${aws_s3_bucket.photo_s3_bucket.arn}/originals/*",
      "${aws_s3_bucket.photo_s3_bucket.arn}/uploads/*"
    ]
  }
  statement {
    principals {
      identifiers = [aws_cloudfront_origin_access_identity.photo_oai.iam_arn]
      type        = "AWS"
    }
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.photo_s3_bucket.arn]
  }
}
