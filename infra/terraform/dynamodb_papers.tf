# DynamoDB table for paper metadata index
# Provisioned via AWS CLI 2026-05-24; this file documents the resource as Terraform.

resource "aws_dynamodb_table" "papers_index" {
  name         = "archimedes-papers-index"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "arxiv_id"

  attribute {
    name = "arxiv_id"
    type = "S"
  }

  attribute {
    name = "cluster_id"
    type = "S"
  }

  attribute {
    name = "year"
    type = "N"
  }

  global_secondary_index {
    name            = "cluster_id-index"
    hash_key        = "cluster_id"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "year-index"
    hash_key        = "year"
    projection_type = "ALL"
  }

  tags = {
    Project = var.project_name
    Purpose = "Paper metadata index for corpus search + KB pipeline"
  }
}
