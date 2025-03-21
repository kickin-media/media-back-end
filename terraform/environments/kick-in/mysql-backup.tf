resource "aws_s3_bucket" "mysql_backup_bucket" {
  bucket = "kickin-media-db-backup"
}

resource "aws_s3_bucket_acl" "mysql_s3_bucket_acl" {
  bucket = aws_s3_bucket.mysql_backup_bucket.bucket
  acl    = "private"
}
resource "aws_s3_bucket_public_access_block" "mysql_s3_bucket_public_acl" {
  bucket                  = aws_s3_bucket.mysql_backup_bucket.bucket
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "mysql_s3_bucket_lifecycle" {
  bucket = aws_s3_bucket.mysql_backup_bucket.bucket
  rule {
    id     = "db-backup-lifecycle-rule"
    status = "Enabled"
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
    noncurrent_version_expiration {
      noncurrent_days = 31
    }
  }
}

resource "aws_iam_user" "mysql_backup_upload_user" {
  name = "${aws_s3_bucket.mysql_backup_bucket.bucket}-db-backup-user"
}

resource "aws_iam_user_policy_attachment" "mysql_backup_user_attachment" {
  policy_arn = aws_iam_policy.mysql_backup_upload_user_policy.arn
  user       = aws_iam_user.mysql_backup_upload_user.name
}

resource "aws_iam_policy" "mysql_backup_upload_user_policy" {
  name = "${aws_s3_bucket.mysql_backup_bucket.bucket}-db-backup-policy"
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow",
        Resource = "${aws_s3_bucket.mysql_backup_bucket.arn}/*"
        Action   = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:HeadObject",
        ]
      },
      {
        Effect   = "Allow",
        Resource = aws_s3_bucket.mysql_backup_bucket.arn
        Action   = "s3:ListBucket"
      }
    ]
  })
}