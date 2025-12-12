# Bootstrap Infrastructure - Terraform State Management
#
# Run this LOCALLY first to create S3 bucket and DynamoDB table
# for Terraform remote state management.
#
# Usage:
#   cd infrastructure/bootstrap
#   terraform init
#   terraform apply

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "AML-Policy-FAQ-Bot"
      Purpose   = "Terraform State Management"
      ManagedBy = "Terraform-Bootstrap"
    }
  }
}

# Variables
variable "aws_region" {
  default = "ap-south-1"
}

variable "project_name" {
  default = "aml-faq-bot"
}

# Data sources
data "aws_caller_identity" "current" {}

# S3 Bucket for Terraform State
resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.project_name}-terraform-state-${data.aws_caller_identity.current.account_id}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket                  = aws_s3_bucket.terraform_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB Table for State Locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "${var.project_name}-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Generate backend config file for other modules
resource "local_file" "backend_config" {
  filename = "${path.module}/../backend/backend.hcl"
  content  = <<-EOT
    bucket         = "${aws_s3_bucket.terraform_state.id}"
    key            = "backend/terraform.tfstate"
    region         = "${var.aws_region}"
    dynamodb_table = "${aws_dynamodb_table.terraform_locks.name}"
    encrypt        = true
  EOT
}

# Outputs
output "state_bucket_name" {
  value = aws_s3_bucket.terraform_state.id
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.terraform_locks.name
}

output "next_steps" {
  value = <<-EOT
    
    Backend config file created at: ../backend/backend.hcl
    
    Now run:
      cd ../backend
      terraform init -backend-config=backend.hcl
      terraform apply
  EOT
}
