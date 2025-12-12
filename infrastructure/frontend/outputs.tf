# Outputs

output "frontend_bucket_name" {
  description = "S3 bucket for frontend static files"
  value       = aws_s3_bucket.frontend.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation)"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "CloudFront domain name (frontend URL)"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}
