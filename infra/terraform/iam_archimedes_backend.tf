# IAM role for backend EC2 — S3 + DynamoDB access
# Provisioned via AWS CLI 2026-05-24; this file documents the resources as Terraform.

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "backend" {
  name        = "archimedes-backend-role"
  description = "Archimedes backend - S3 + DynamoDB access for corpus pipeline"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_iam_role_policy" "backend_s3_dynamodb" {
  name = "archimedes-s3-dynamodb-access"
  role = aws_iam_role.backend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3CorpusAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject",
        ]
        Resource = [
          aws_s3_bucket.corpus_artifacts.arn,
          "${aws_s3_bucket.corpus_artifacts.arn}/*",
          aws_s3_bucket.paper_pdfs.arn,
          "${aws_s3_bucket.paper_pdfs.arn}/*",
        ]
      },
      {
        Sid    = "DynamoDBPapersAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
        ]
        Resource = [
          aws_dynamodb_table.papers_index.arn,
          "${aws_dynamodb_table.papers_index.arn}/index/*",
        ]
      },
    ]
  })
}

resource "aws_iam_instance_profile" "backend" {
  name = "archimedes-backend-profile"
  role = aws_iam_role.backend.name
}
