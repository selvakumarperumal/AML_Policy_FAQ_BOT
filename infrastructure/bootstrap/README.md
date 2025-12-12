# Bootstrap Infrastructure - README
#
# This creates the S3 bucket and DynamoDB table for Terraform remote state.
# Run this LOCALLY before any other infrastructure.

## Prerequisites
- AWS CLI configured with appropriate credentials
- Terraform >= 1.0

## Usage

```bash
cd infrastructure/bootstrap
terraform init
terraform apply
```

## After Bootstrap

Copy the backend configuration from the output and update `infrastructure/backend/main.tf`:

```hcl
terraform {
  backend "s3" {
    bucket         = "<state-bucket-name>"
    key            = "backend/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "<locks-table-name>"
    encrypt        = true
  }
}
```

## Resources Created

| Resource | Purpose |
|----------|---------|
| S3 Bucket | Stores Terraform state files |
| DynamoDB Table | State locking to prevent concurrent modifications |

## Important Notes

- Resources have `prevent_destroy = true` lifecycle rule
- S3 bucket has versioning enabled for state history
- Both resources are encrypted
