# CloudFront Distribution for Frontend

# Origin Access Control (OAC) for secure S3 access
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.project_name}-frontend-oac"
  description                       = "OAC for frontend S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100" # Use only edge locations in NA/EU (cheapest)
  comment             = "${var.project_name} Frontend"

  # S3 Origin
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.frontend.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  # Default cache behavior
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.frontend.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    # Cache policy - optimized for static content
    cache_policy_id          = aws_cloudfront_cache_policy.frontend.id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.frontend.id
  }

  # SPA routing - serve index.html for all 404s
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  # Geo restriction (none)
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL Certificate (CloudFront default)
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${var.project_name}-frontend"
  }
}

# Cache Policy - optimized for static assets
resource "aws_cloudfront_cache_policy" "frontend" {
  name        = "${var.project_name}-frontend-cache-policy"
  min_ttl     = 1
  default_ttl = 86400    # 1 day
  max_ttl     = 31536000 # 1 year

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }
    headers_config {
      header_behavior = "none"
    }
    query_strings_config {
      query_string_behavior = "none"
    }
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true
  }
}

# Origin Request Policy
resource "aws_cloudfront_origin_request_policy" "frontend" {
  name = "${var.project_name}-frontend-origin-policy"

  cookies_config {
    cookie_behavior = "none"
  }
  headers_config {
    header_behavior = "none"
  }
  query_strings_config {
    query_string_behavior = "none"
  }
}
