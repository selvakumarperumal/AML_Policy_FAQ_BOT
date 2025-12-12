# S3 Bucket for Chroma DB

resource "aws_s3_bucket" "documents" {
  bucket        = "${var.project_name}-data-${var.environment}-${data.aws_caller_identity.current.account_id}"
  force_destroy = var.environment != "prod"
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket                  = aws_s3_bucket.documents.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Secrets Manager for NVIDIA credentials
resource "aws_secretsmanager_secret" "app_config" {
  name                    = "${var.project_name}/config-${var.environment}"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "app_config" {
  secret_id = aws_secretsmanager_secret.app_config.id
  secret_string = jsonencode({
    NVIDIA_API_KEY              = var.nvidia_api_key
    NVIDIA_MODEL_NAME           = var.nvidia_model_name
    NVIDIA_EMBEDDING_MODEL_NAME = var.nvidia_embedding_model_name
  })
}
