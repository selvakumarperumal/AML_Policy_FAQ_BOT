# =============================================================================
# LAMBDA FUNCTION - AML Policy FAQ Bot Backend
# =============================================================================
# DEPLOYMENT STRATEGY:
# - Terraform creates the Lambda function with placeholder code
# - GitHub Actions deploys the real application code
# - This separation allows infrastructure and code to be managed independently
# =============================================================================

# -----------------------------------------------------------------------------
# PLACEHOLDER DEPLOYMENT PACKAGE
# -----------------------------------------------------------------------------
# Creates a minimal zip file for initial Lambda creation.
# Real application code is deployed via GitHub Actions using:
#   aws lambda update-function-code --function-name ... --zip-file ...
# -----------------------------------------------------------------------------
data "archive_file" "lambda_placeholder" {
  type        = "zip"
  output_path = "${path.module}/placeholder.zip"

  source {
    content  = <<-EOF
      def handler(event, context):
          return {
              "statusCode": 503,
              "body": "Application not deployed yet. Run GitHub Actions deploy-backend workflow."
          }
    EOF
    filename = "handler.py"
  }
}

# -----------------------------------------------------------------------------
# LAMBDA FUNCTION
# -----------------------------------------------------------------------------
resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api-${var.environment}"
  description   = "AML Policy FAQ Bot API"

  # Placeholder code - real code deployed via GitHub Actions
  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256

  runtime     = "python3.12"
  handler     = "handler.handler"
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  role = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      CONFIG_SECRET_NAME = aws_secretsmanager_secret.app_config.name
      S3_BUCKET          = aws_s3_bucket.documents.id
      ENVIRONMENT        = var.environment
    }
  }

  # Ignore changes to code since GitHub Actions manages deployment
  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  tags = {
    Name = "${var.project_name}-api"
  }
}

# -----------------------------------------------------------------------------
# LAMBDA FUNCTION URL
# -----------------------------------------------------------------------------
resource "aws_lambda_function_url" "api" {
  function_name      = aws_lambda_function.api.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["*"] # Use wildcard to avoid AWS validation constraints
    allow_headers = ["*"]
    max_age       = 3600
  }
}

# Note: CloudWatch Logs disabled to reduce costs
# Lambda logs are still available via AWS Console if needed
