# AI Interview Tool - Azure Infrastructure
# デモ環境デプロイ用（Azure専用）

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.14"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # デモ/開発環境ではローカル backend を使用
  # 本番環境では以下のように azurerm backend に切り替えること:
  #   backend "azurerm" {
  #     resource_group_name  = "terraform-state-rg"
  #     storage_account_name = "tfstateXXXXXX"
  #     container_name       = "tfstate"
  #     key                  = "ai-interviewer.tfstate"
  #   }
  backend "local" {}
}

# Variables
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
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

# cloud_provider variable kept for tfvars compatibility
variable "cloud_provider" {
  description = "Primary cloud provider (azure, aws, gcp)"
  type        = string
  default     = "azure"
}

# Local values
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  resource_prefix = "${var.project_name}-${var.environment}"
}

# Random suffix for globally unique names
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Azure module (direct call without count)
module "azure" {
  source = "./modules/azure"

  environment     = var.environment
  resource_prefix = local.resource_prefix
  location        = var.region
  tags            = local.common_tags
  suffix          = random_string.suffix.result
  ai_provider     = var.ai_provider
}

# Outputs
output "cloud_provider" {
  description = "Selected cloud provider"
  value       = "azure"
}

output "api_endpoint" {
  description = "API endpoint URL"
  value       = module.azure.api_endpoint
}

output "database_connection" {
  description = "Database connection string (sensitive)"
  value       = module.azure.database_connection
  sensitive   = true
}

output "container_registry" {
  description = "Container registry URL"
  value       = module.azure.container_registry
}

output "resource_group_name" {
  description = "Resource group name"
  value       = module.azure.resource_group_name
}
