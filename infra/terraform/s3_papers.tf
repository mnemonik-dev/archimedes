# S3 buckets for paper corpus artifacts and PDFs
# Provisioned via AWS CLI 2026-05-24; this file documents the resources as Terraform.

resource "aws_s3_bucket" "corpus_artifacts" {
  bucket = "archimedes-corpus-artifacts-prod"

  tags = {
    Project = var.project_name
    Purpose = "KB pipeline artifacts (embeddings, clusters, topics, KG)"
  }
}

resource "aws_s3_bucket_versioning" "corpus_artifacts" {
  bucket = aws_s3_bucket.corpus_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "corpus_artifacts" {
  bucket                  = aws_s3_bucket.corpus_artifacts.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "paper_pdfs" {
  bucket = "archimedes-paper-pdfs-prod"

  tags = {
    Project = var.project_name
    Purpose = "Raw paper PDFs from arxiv ingest"
  }
}

resource "aws_s3_bucket_versioning" "paper_pdfs" {
  bucket = aws_s3_bucket.paper_pdfs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "paper_pdfs" {
  bucket                  = aws_s3_bucket.paper_pdfs.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}
