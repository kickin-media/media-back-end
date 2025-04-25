resource "aws_iam_policy" "upload_role_policy" {
  name = "${aws_s3_bucket.frontend_s3_bucket.bucket}-upload-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow",
        Resource = "${aws_s3_bucket.frontend_s3_bucket.arn}/*"
        Action = [
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

resource "aws_iam_role_policy_attachment" "upload_role_attachment" {
  policy_arn = aws_iam_policy.upload_role_policy.arn
  role       = aws_iam_role.frontend_upload_role.name
}

data "aws_iam_openid_connect_provider" "example" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_role" "frontend_upload_role" {
  name = "${aws_s3_bucket.frontend_s3_bucket.bucket}-upload-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "sts:AssumeRoleWithWebIdentity"
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.example.arn
        }
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.frontend_workflow_repo}:*"
          }
        }
      }
    ]
  })
  force_detach_policies = true
}