resource "aws_iam_user" "upload_user" {
  name = "${aws_s3_bucket.frontend_s3_bucket.bucket}-upload-user"
}

resource "aws_iam_user_policy_attachment" "upload_user_attachment" {
  policy_arn = aws_iam_policy.upload_user_policy.arn
  user       = aws_iam_user.upload_user.name
}

resource "aws_iam_policy" "upload_user_policy" {
  name = "${aws_s3_bucket.frontend_s3_bucket.bucket}-upload-policy"
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow",
        Resource = "${aws_s3_bucket.frontend_s3_bucket.arn}/*"
        Action   = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:GetObject",
          "s3:HeadObject",
          "s3:DeleteObject",
        ]
      },
      {
        Effect   = "Allow",
        Resource = aws_s3_bucket.frontend_s3_bucket.arn
        Action   = "s3:ListBucket"
      },
      {
        Effect   = "Allow",
        Resource = aws_cloudfront_distribution.frontend_cloudfront_distribution.arn
        Action   = "cloudfront:CreateInvalidation"
      }
    ]
  })
}