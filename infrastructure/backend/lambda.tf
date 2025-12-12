# Lambda Function

resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api-${var.environment}"
  description   = "AML Policy FAQ Bot API"

  filename         = "${path.module}/../../backend/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../../backend/lambda.zip")

  runtime     = "python3.12"
  handler     = "handler.handler"
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  role = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      CONFIG_SECRET_NAME = aws_secretsmanager_secret.app_config.name
      S3_BUCKET          = aws_s3_bucket.documents.id
      VECTOR_STORE_PATH  = "/tmp/chroma_db"
    }
  }
}

# Lambda function URL
resource "aws_lambda_function_url" "api" {
  function_name      = aws_lambda_function.api.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
    max_age       = 3600
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = 14
}
