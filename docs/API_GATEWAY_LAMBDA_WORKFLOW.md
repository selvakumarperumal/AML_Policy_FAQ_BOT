# API Gateway ↔ Lambda Integration Workflow

This document explains how AWS API Gateway HTTP API connects to AWS Lambda in the AML Policy FAQ Bot infrastructure.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Request Flow](#request-flow)
3. [Terraform Resources](#terraform-resources)
4. [Lambda Permission (Resource-Based Policy)](#lambda-permission-resource-based-policy)
5. [Source ARN Pattern Explained](#source-arn-pattern-explained)
6. [CORS Configuration](#cors-configuration)
7. [Deployment Workflow](#deployment-workflow)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐
│   Frontend   │────▶│   API Gateway     │────▶│      Lambda      │
│   (Browser)  │     │   (HTTP API)      │     │   (FastAPI)      │
│              │     │                   │     │                  │
│   React/JS   │◀────│   CORS enabled    │◀────│   Mangum adapter │
└──────────────┘     └───────────────────┘     └──────────────────┘
      HTTPS              AWS_PROXY               Python 3.12
```

### Components

| Component | Service | Purpose |
|-----------|---------|---------|
| API Gateway | `aws_apigatewayv2_api` | Receives HTTP requests, handles CORS |
| Integration | `aws_apigatewayv2_integration` | Connects API Gateway to Lambda |
| Route | `aws_apigatewayv2_route` | Directs requests to integration |
| Stage | `aws_apigatewayv2_stage` | Deployment stage (`$default`) |
| Permission | `aws_lambda_permission` | Allows API Gateway to invoke Lambda |

---

## Request Flow

### Step-by-Step Request Journey

```
1. User Request
   │
   │  GET https://abc123.execute-api.ap-south-1.amazonaws.com/docs
   ▼
2. API Gateway Receives Request
   │
   │  - Validates CORS headers
   │  - Matches route ($default = catch-all)
   │  - Finds integration (Lambda)
   ▼
3. API Gateway Invokes Lambda
   │
   │  - Checks permission (aws_lambda_permission)
   │  - Sends event via AWS_PROXY format
   ▼
4. Lambda Executes
   │
   │  - Mangum wraps ASGI event
   │  - FastAPI processes request
   │  - Returns response
   ▼
5. Response Returns
   │
   │  - API Gateway adds CORS headers
   │  - Returns to user
   ▼
6. User Receives Response
```

### Event Format (AWS_PROXY v2.0)

When API Gateway invokes Lambda, it sends this event structure:

```json
{
  "version": "2.0",
  "routeKey": "$default",
  "rawPath": "/docs",
  "rawQueryString": "",
  "headers": {
    "host": "abc123.execute-api.ap-south-1.amazonaws.com",
    "user-agent": "Mozilla/5.0...",
    "accept": "text/html"
  },
  "requestContext": {
    "http": {
      "method": "GET",
      "path": "/docs"
    },
    "stage": "$default"
  },
  "isBase64Encoded": false
}
```

---

## Terraform Resources

### 1. API Gateway HTTP API

```hcl
resource "aws_apigatewayv2_api" "http" {
  name          = "aml-faq-bot-http-api-dev"
  protocol_type = "HTTP"          # HTTP API (not REST API)

  cors_configuration {
    allow_origins  = ["*"]        # Allow all origins
    allow_methods  = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers  = ["*"]
    expose_headers = ["*"]
    max_age        = 3600         # Cache preflight for 1 hour
  }
}
```

### 2. Lambda Integration

```hcl
resource "aws_apigatewayv2_integration" "lambda" {
  api_id           = aws_apigatewayv2_api.http.id
  integration_type = "AWS_PROXY"                        # Full request proxied
  integration_uri  = aws_lambda_function.api.invoke_arn # Lambda ARN
  integration_method     = "POST"                       # Always POST for Lambda
  payload_format_version = "2.0"                        # Modern format
}
```

**Integration Types:**

| Type | Description |
|------|-------------|
| `AWS_PROXY` | Full request/response proxied to Lambda (recommended) |
| `AWS` | Manual request/response mapping |
| `HTTP_PROXY` | Proxy to HTTP backend |
| `HTTP` | HTTP with request/response transforms |

### 3. Route (Catch-All)

```hcl
resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "$default"    # Matches ALL paths and methods
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}
```

**Route Examples:**

| Route Key | Matches |
|-----------|---------|
| `$default` | Everything (catch-all) |
| `GET /users` | Only GET /users |
| `POST /api/{proxy+}` | POST /api/* with wildcard |
| `ANY /health` | Any method on /health |

### 4. Stage (Auto-Deploy)

```hcl
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true    # Auto-deploy on changes
}
```

---

## Lambda Permission (Resource-Based Policy)

This is the **critical piece** that allows API Gateway to invoke Lambda.

### The Permission Resource

```hcl
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
```

### Field-by-Field Explanation

| Field | Value | Explanation |
|-------|-------|-------------|
| `statement_id` | `AllowAPIGatewayInvoke` | Unique identifier for this permission |
| `action` | `lambda:InvokeFunction` | The IAM action being allowed |
| `function_name` | `aml-faq-bot-api-dev` | Which Lambda function to allow access to |
| `principal` | `apigateway.amazonaws.com` | Who is allowed (API Gateway service) |
| `source_arn` | See below | Which specific API Gateway resources |

### What Permission Creates

When applied, this creates a **resource-based policy** on the Lambda function:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAPIGatewayInvoke",
      "Effect": "Allow",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:ap-south-1:123456789012:function:aml-faq-bot-api-dev",
      "Condition": {
        "ArnLike": {
          "AWS:SourceArn": "arn:aws:execute-api:ap-south-1:123456789012:abc123/*/*"
        }
      }
    }
  ]
}
```

---

## Source ARN Pattern Explained

### ARN Structure

```
arn:aws:execute-api:ap-south-1:123456789012:abc123/*/*
└─┬─┘ └┬┘ └────┬────┘ └───┬───┘ └────┬─────┘ └──┬──┘└┬┘└┬┘
  │    │       │          │          │          │   │  │
  │    │       │          │          │          │   │  └── Path pattern
  │    │       │          │          │          │   └───── HTTP method
  │    │       │          │          │          └───────── Stage
  │    │       │          │          └──────────────────── API ID
  │    │       │          └─────────────────────────────── Account ID
  │    │       └────────────────────────────────────────── Region
  │    └────────────────────────────────────────────────── Service
  └─────────────────────────────────────────────────────── Partition
```

### Pattern Breakdown: `/*/*`

```
${aws_apigatewayv2_api.http.execution_arn}/*/*
                                          │ │
                                          │ └── /* = Any path
                                          └──── /* = Any method (GET, POST, etc.)
```

### Pattern Examples

| Pattern | Meaning | Example Matches |
|---------|---------|-----------------|
| `/*/*` | Any method, any path | `GET /docs`, `POST /api/v1/query` |
| `/*/docs` | Any method, only /docs | `GET /docs`, `POST /docs` |
| `/GET/*` | Only GET, any path | `GET /health`, `GET /api/v1/query` |
| `/POST/api/v1/query` | Only POST to /api/v1/query | `POST /api/v1/query` |
| `/$default/*/*` | Stage-specific | Only default stage |

### Restrictive vs Permissive

**Most Permissive (Current):**
```hcl
source_arn = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
# Allows: Any method, any path
```

**More Restrictive Example:**
```hcl
source_arn = "${aws_apigatewayv2_api.http.execution_arn}/*/api/*"
# Allows: Any method, but only paths starting with /api/
```

**Most Restrictive:**
```hcl
source_arn = "${aws_apigatewayv2_api.http.execution_arn}/POST/api/v1/query"
# Allows: Only POST to /api/v1/query
```

---

## CORS Configuration

### What is CORS?

Cross-Origin Resource Sharing allows your frontend (e.g., `http://localhost:3000`) to call your API (e.g., `https://abc123.execute-api.ap-south-1.amazonaws.com`).

### Configuration in API Gateway

```hcl
cors_configuration {
  allow_origins  = ["*"]                                    # Who can call
  allow_methods  = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]  # Which methods
  allow_headers  = ["*"]                                    # Which headers
  expose_headers = ["*"]                                    # Headers in response
  max_age        = 3600                                     # Preflight cache (1h)
}
```

### CORS Flow

```
1. Browser: OPTIONS /api/v1/query (Preflight)
   │
   │  Access-Control-Request-Method: POST
   │  Access-Control-Request-Headers: Content-Type
   ▼
2. API Gateway: Returns CORS headers
   │
   │  Access-Control-Allow-Origin: *
   │  Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
   │  Access-Control-Allow-Headers: *
   ▼
3. Browser: POST /api/v1/query (Actual request)
   │
   │  Content-Type: application/json
   │  Body: {"question": "What is AML?"}
   ▼
4. API Gateway → Lambda → Response with CORS headers
```

---

## Deployment Workflow

### GitHub Actions Workflows

```
┌─────────────────────────┐     ┌─────────────────────────┐
│   Infrastructure.yml     │     │   Deploy-Backend.yml    │
│                         │     │                         │
│   1. Terraform Plan     │     │   1. Test (uv sync)     │
│   2. Terraform Apply    │────▶│   2. Build (zip)        │
│   3. Output API URL     │     │   3. Deploy to Lambda   │
│                         │     │   4. Show API URL       │
└─────────────────────────┘     └─────────────────────────┘
       Run First                      Run Second
```

### Step 1: Infrastructure (Run Once)

```yaml
# .github/workflows/infrastructure.yml
- terraform init -backend-config=backend.hcl
- terraform plan -var="..."
- terraform apply -auto-approve tfplan
```

**Creates:**
- API Gateway HTTP API
- Lambda Function (placeholder)
- S3 Bucket
- Secrets Manager
- IAM Roles and Policies
- Lambda Permission (API Gateway → Lambda)

### Step 2: Deploy Backend (Run on Each Code Change)

```yaml
# .github/workflows/deploy-backend.yml
- uv sync                           # Install deps
- uv pip install --target ...       # Create package
- zip -r lambda.zip .               # Create ZIP
- aws lambda update-function-code   # Deploy
- terraform output api_gateway_url  # Get URL
```

---

## Troubleshooting

### Common Errors

#### 1. 403 Forbidden from Lambda Function URL

**Cause:** Lambda Function URL requires explicit permission for public access.

**Solution:** Use API Gateway URL instead (already has permission).

```
✗ https://xxx.lambda-url.ap-south-1.on.aws/     # 403 Forbidden
✓ https://xxx.execute-api.ap-south-1.amazonaws.com/  # Works!
```

#### 2. 500 Internal Server Error

**Cause:** Lambda function error.

**Debug:** Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/aml-faq-bot-api-dev --follow
```

#### 3. CORS Error in Browser

**Cause:** Origins not allowed or missing headers.

**Check:** API Gateway CORS configuration includes your frontend origin.

#### 4. Timeout (504)

**Cause:** Lambda execution exceeds API Gateway timeout (29 seconds).

**Solution:** Increase Lambda timeout or optimize code:
```hcl
variable "lambda_timeout" {
  default = 30  # seconds
}
```

---

## Quick Reference

### URLs

| Type | URL Pattern |
|------|-------------|
| API Gateway | `https://{api-id}.execute-api.{region}.amazonaws.com` |
| Lambda URL | `https://{function-url-id}.lambda-url.{region}.on.aws` |

### Endpoints

| Endpoint | URL |
|----------|-----|
| Swagger UI | `/docs` |
| ReDoc | `/redoc` |
| Health Check | `/api/v1/health` |
| Query | `POST /api/v1/query` |
| Ingest | `POST /api/v1/ingest` |

### AWS CLI Commands

```bash
# List APIs
aws apigatewayv2 get-apis --region ap-south-1

# Get Lambda permission
aws lambda get-policy --function-name aml-faq-bot-api-dev

# Test endpoint
curl https://xxx.execute-api.ap-south-1.amazonaws.com/api/v1/health
```

---

## Summary

1. **API Gateway** receives HTTP requests from users
2. **Integration** (AWS_PROXY) forwards full request to Lambda
3. **Route** ($default) catches all paths
4. **Permission** allows API Gateway to invoke Lambda
5. **Lambda** runs FastAPI via Mangum adapter
6. **Response** flows back through API Gateway with CORS headers

The key security component is the **Lambda Permission** which explicitly allows only the specified API Gateway to invoke the Lambda function.
