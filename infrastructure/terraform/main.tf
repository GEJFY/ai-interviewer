# AI Interview Tool - Multi-Cloud Infrastructure
# Terraform configuration for Azure, AWS, and GCP deployments

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.14"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.82"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 6.14"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  backend "azurerm" {
    # Configure backend in environment-specific tfvars
  }
}

# Variables
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "cloud_provider" {
  description = "Primary cloud provider (azure, aws, gcp)"
  type        = string
  default     = "azure"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "ai-interviewer"
}

variable "region" {
  description = "Primary deployment region"
  type        = string
  default     = "japaneast"
}

variable "ai_provider" {
  description = "AI/LLM provider (azure_openai, aws_bedrock, gcp_vertex, anthropic)"
  type        = string
  default     = "azure_openai"
}

# Local values
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    CreatedAt   = timestamp()
  }

  resource_prefix = "${var.project_name}-${var.environment}"
}

# Random suffix for globally unique names
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Conditional module loading based on cloud provider
module "azure" {
  source = "./modules/azure"
  count  = var.cloud_provider == "azure" ? 1 : 0

  environment     = var.environment
  resource_prefix = local.resource_prefix
  location        = var.region
  tags            = local.common_tags
  suffix          = random_string.suffix.result
  ai_provider     = var.ai_provider
}

module "aws" {
  source = "./modules/aws"
  count  = var.cloud_provider == "aws" ? 1 : 0

  environment     = var.environment
  resource_prefix = local.resource_prefix
  region          = var.region
  tags            = local.common_tags
  suffix          = random_string.suffix.result
  ai_provider     = var.ai_provider
}

module "gcp" {
  source = "./modules/gcp"
  count  = var.cloud_provider == "gcp" ? 1 : 0

  environment     = var.environment
  resource_prefix = local.resource_prefix
  region          = var.region
  labels          = local.common_tags
  suffix          = random_string.suffix.result
  ai_provider     = var.ai_provider
}

# Outputs
output "cloud_provider" {
  description = "Selected cloud provider"
  value       = var.cloud_provider
}

output "api_endpoint" {
  description = "API endpoint URL"
  value = var.cloud_provider == "azure" ? (
    length(module.azure) > 0 ? module.azure[0].api_endpoint : null
  ) : var.cloud_provider == "aws" ? (
    length(module.aws) > 0 ? module.aws[0].api_endpoint : null
  ) : (
    length(module.gcp) > 0 ? module.gcp[0].api_endpoint : null
  )
}

output "database_connection" {
  description = "Database connection string (sensitive)"
  value = var.cloud_provider == "azure" ? (
    length(module.azure) > 0 ? module.azure[0].database_connection : null
  ) : var.cloud_provider == "aws" ? (
    length(module.aws) > 0 ? module.aws[0].database_connection : null
  ) : (
    length(module.gcp) > 0 ? module.gcp[0].database_connection : null
  )
  sensitive = true
}
