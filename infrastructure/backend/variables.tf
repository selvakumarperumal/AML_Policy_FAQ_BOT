# Variables

variable "aws_region" {
  default = "ap-south-1"
}

variable "environment" {
  default = "dev"
}

variable "project_name" {
  default = "aml-faq-bot"
}

variable "lambda_memory_size" {
  default = 1024
}

variable "lambda_timeout" {
  default = 30
}

# Secrets (from GitHub Actions)
variable "nvidia_api_key" {
  type      = string
  sensitive = true
}

variable "nvidia_model_name" {
  type    = string
  default = "meta/llama-3.1-70b-instruct"
}

variable "nvidia_embedding_model_name" {
  type    = string
  default = "nvidia/nv-embedqa-e5-v5"
}
