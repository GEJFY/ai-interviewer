# Azure Infrastructure Module for AI Interview Tool

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.14"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

# Variables
variable "environment" {
  type = string
}

variable "resource_prefix" {
  type = string
}

variable "location" {
  type    = string
  default = "japaneast"
}

variable "tags" {
  type = map(string)
}

variable "suffix" {
  type = string
}

variable "ai_provider" {
  type = string
}

variable "alert_email" {
  type        = string
  default     = "admin@example.com"
  description = "Email address for monitoring alerts"
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${var.resource_prefix}-rg"
  location = var.location
  tags     = var.tags
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = "${var.resource_prefix}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = var.tags
}

resource "azurerm_subnet" "app" {
  name                 = "app-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]

  delegation {
    name = "app-delegation"
    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

resource "azurerm_subnet" "db" {
  name                 = "db-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]

  delegation {
    name = "db-delegation"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                       = "${var.resource_prefix}-kv-${var.suffix}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  rbac_authorization_enabled = true

  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }

  tags = var.tags
}

data "azurerm_client_config" "current" {}

# PostgreSQL Flexible Server
resource "azurerm_private_dns_zone" "postgres" {
  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "postgres-vnet-link"
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.main.id
  resource_group_name   = azurerm_resource_group.main.name
  registration_enabled  = false
}

resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "azurerm_postgresql_flexible_server" "main" {
  name                          = "${var.resource_prefix}-db-${var.suffix}"
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  version                       = "16"
  delegated_subnet_id           = azurerm_subnet.db.id
  private_dns_zone_id           = azurerm_private_dns_zone.postgres.id
  administrator_login           = "aiinterviewer"
  administrator_password        = random_password.db_password.result
  zone                          = "1"
  storage_mb                    = 32768
  sku_name                      = var.environment == "prod" ? "GP_Standard_D4s_v3" : "B_Standard_B2s"
  backup_retention_days         = var.environment == "prod" ? 35 : 7
  geo_redundant_backup_enabled  = var.environment == "prod"

  tags = var.tags

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = "aiinterviewer"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Enable pgvector extension
resource "azurerm_postgresql_flexible_server_configuration" "extensions" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "vector,uuid-ossp"
}

# Redis Cache
resource "azurerm_redis_cache" "main" {
  name                = "${var.resource_prefix}-redis-${var.suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = var.environment == "prod" ? 2 : 0
  family              = var.environment == "prod" ? "C" : "C"
  sku_name            = var.environment == "prod" ? "Standard" : "Basic"
  non_ssl_port_enabled = false
  minimum_tls_version = "1.2"

  redis_configuration {
    maxmemory_policy = "volatile-lru"
  }

  tags = var.tags
}

# Storage Account
resource "azurerm_storage_account" "main" {
  name                            = "aiint${var.suffix}${var.environment}"
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_tier                    = "Standard"
  account_replication_type        = var.environment == "prod" ? "GRS" : "LRS"
  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"

  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = 7
    }
  }

  tags = var.tags
}

resource "azurerm_storage_container" "audio" {
  name                  = "audio-files"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "reports" {
  name                  = "reports"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

# Azure AI Foundry / Azure OpenAI (if selected)
resource "azurerm_cognitive_account" "openai" {
  count               = var.ai_provider == "azure_openai" ? 1 : 0
  name                = "${var.resource_prefix}-openai-${var.suffix}"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "OpenAI"
  sku_name            = "S0"

  tags = var.tags
}

# GPT-5.2 - Latest Flagship Model
resource "azurerm_cognitive_deployment" "gpt52" {
  count                = var.ai_provider == "azure_openai" ? 1 : 0
  name                 = "gpt-5.2"
  cognitive_account_id = azurerm_cognitive_account.openai[0].id

  model {
    format  = "OpenAI"
    name    = "gpt-5.2"
    version = "2026-01-15"
  }

  sku {
    name     = "Standard"
    capacity = 50
  }
}

# GPT-5 Nano - Ultra-efficient Model
resource "azurerm_cognitive_deployment" "gpt5nano" {
  count                = var.ai_provider == "azure_openai" ? 1 : 0
  name                 = "gpt-5-nano"
  cognitive_account_id = azurerm_cognitive_account.openai[0].id

  model {
    format  = "OpenAI"
    name    = "gpt-5-nano"
    version = "2026-01-15"
  }

  sku {
    name     = "Standard"
    capacity = 200
  }
}

# GPT-4o - Still widely used
resource "azurerm_cognitive_deployment" "gpt4o" {
  count                = var.ai_provider == "azure_openai" ? 1 : 0
  name                 = "gpt-4o"
  cognitive_account_id = azurerm_cognitive_account.openai[0].id

  model {
    format  = "OpenAI"
    name    = "gpt-4o"
    version = "2024-11-20"
  }

  sku {
    name     = "Standard"
    capacity = 30
  }
}

# Claude Sonnet 4.6 Opus via Azure AI Foundry
resource "azurerm_cognitive_deployment" "claude_sonnet_46_opus" {
  count                = var.ai_provider == "azure_openai" ? 1 : 0
  name                 = "claude-sonnet-4.6-opus"
  cognitive_account_id = azurerm_cognitive_account.openai[0].id

  model {
    format  = "Anthropic"
    name    = "claude-sonnet-4.6-opus"
    version = "2026-01-01"
  }

  sku {
    name     = "Standard"
    capacity = 30
  }
}

# Claude 4.6 Sonnet via Azure AI Foundry
resource "azurerm_cognitive_deployment" "claude_46_sonnet" {
  count                = var.ai_provider == "azure_openai" ? 1 : 0
  name                 = "claude-4.6-sonnet"
  cognitive_account_id = azurerm_cognitive_account.openai[0].id

  model {
    format  = "Anthropic"
    name    = "claude-4.6-sonnet"
    version = "2026-01-01"
  }

  sku {
    name     = "Standard"
    capacity = 50
  }
}

# Embedding Model
resource "azurerm_cognitive_deployment" "embedding" {
  count                = var.ai_provider == "azure_openai" ? 1 : 0
  name                 = "text-embedding-3-large"
  cognitive_account_id = azurerm_cognitive_account.openai[0].id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-large"
    version = "1"
  }

  sku {
    name     = "Standard"
    capacity = 120
  }
}

# Azure Speech Service
resource "azurerm_cognitive_account" "speech" {
  name                = "${var.resource_prefix}-speech-${var.suffix}"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "SpeechServices"
  sku_name            = "S0"

  tags = var.tags
}

# Container Registry
resource "azurerm_container_registry" "main" {
  name                = "aiinterviewer${var.suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.environment == "prod" ? "Premium" : "Basic"
  admin_enabled       = true

  tags = var.tags
}

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "${var.resource_prefix}-plan"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = var.environment == "prod" ? "P2v3" : "B2"

  tags = var.tags
}

# Web App for Backend API
resource "azurerm_linux_web_app" "api" {
  name                      = "${var.resource_prefix}-api-${var.suffix}"
  resource_group_name       = azurerm_resource_group.main.name
  location                  = azurerm_resource_group.main.location
  service_plan_id           = azurerm_service_plan.main.id
  virtual_network_subnet_id = azurerm_subnet.app.id
  https_only                = true

  site_config {
    always_on                         = var.environment == "prod"
    health_check_path                 = "/api/v1/health"
    container_registry_use_managed_identity = true

    application_stack {
      docker_image_name        = "ai-interviewer-api:latest"
      docker_registry_url      = "https://${azurerm_container_registry.main.login_server}"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    WEBSITES_ENABLE_APP_SERVICE_STORAGE = "false"
    DOCKER_REGISTRY_SERVER_URL          = "https://${azurerm_container_registry.main.login_server}"

    DATABASE_URL             = "postgresql+asyncpg://${azurerm_postgresql_flexible_server.main.administrator_login}@${azurerm_postgresql_flexible_server.main.name}/${azurerm_postgresql_flexible_server_database.main.name}"
    REDIS_URL                = "rediss://:${azurerm_redis_cache.main.primary_access_key}@${azurerm_redis_cache.main.hostname}:${azurerm_redis_cache.main.ssl_port}"
    AZURE_STORAGE_CONNECTION = azurerm_storage_account.main.primary_connection_string
    AZURE_SPEECH_KEY         = azurerm_cognitive_account.speech.primary_access_key
    AZURE_SPEECH_REGION      = var.location

    AI_PROVIDER = var.ai_provider
  }

  tags = var.tags
}

# Static Web App for Frontend
resource "azurerm_static_web_app" "web" {
  name                = "${var.resource_prefix}-web-${var.suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = "eastasia"
  sku_tier            = var.environment == "prod" ? "Standard" : "Free"
  sku_size            = var.environment == "prod" ? "Standard" : "Free"

  tags = var.tags
}

# Application Insights
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.resource_prefix}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.tags
}

resource "azurerm_application_insights" "main" {
  name                = "${var.resource_prefix}-insights"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"

  tags = var.tags
}

# =============================================================================
# Monitoring and Alerting
# =============================================================================

# Action Group for Alerts
resource "azurerm_monitor_action_group" "main" {
  name                = "${var.resource_prefix}-alerts"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "aiintervw"

  email_receiver {
    name                    = "admin"
    email_address           = var.alert_email
    use_common_alert_schema = true
  }

  tags = var.tags
}

# API Health Alert
resource "azurerm_monitor_metric_alert" "api_health" {
  name                = "${var.resource_prefix}-api-health"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.api.id]
  description         = "Alert when API health check fails"
  severity            = 1
  frequency           = "PT1M"
  window_size         = "PT5M"

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "HealthCheckStatus"
    aggregation      = "Average"
    operator         = "LessThan"
    threshold        = 100
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  tags = var.tags
}

# API Response Time Alert
resource "azurerm_monitor_metric_alert" "api_response_time" {
  name                = "${var.resource_prefix}-api-latency"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.api.id]
  description         = "Alert when API response time exceeds threshold"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "HttpResponseTime"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 5  # 5 seconds
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  tags = var.tags
}

# Database CPU Alert
resource "azurerm_monitor_metric_alert" "db_cpu" {
  name                = "${var.resource_prefix}-db-cpu"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_postgresql_flexible_server.main.id]
  description         = "Alert when database CPU usage is high"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"

  criteria {
    metric_namespace = "Microsoft.DBforPostgreSQL/flexibleServers"
    metric_name      = "cpu_percent"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  tags = var.tags
}

# Redis Memory Alert
resource "azurerm_monitor_metric_alert" "redis_memory" {
  name                = "${var.resource_prefix}-redis-memory"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_redis_cache.main.id]
  description         = "Alert when Redis memory usage is high"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"

  criteria {
    metric_namespace = "Microsoft.Cache/redis"
    metric_name      = "usedmemorypercentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  tags = var.tags
}

# Application Insights Smart Detection
resource "azurerm_application_insights_smart_detection_rule" "failure_anomalies" {
  name                    = "Slow page load time"
  application_insights_id = azurerm_application_insights.main.id
  enabled                 = true
}

# Diagnostic Settings for API
resource "azurerm_monitor_diagnostic_setting" "api" {
  name                       = "${var.resource_prefix}-api-diag"
  target_resource_id         = azurerm_linux_web_app.api.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log {
    category = "AppServiceHTTPLogs"
  }

  enabled_log {
    category = "AppServiceConsoleLogs"
  }

  enabled_log {
    category = "AppServiceAppLogs"
  }

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

# Diagnostic Settings for Database
resource "azurerm_monitor_diagnostic_setting" "db" {
  name                       = "${var.resource_prefix}-db-diag"
  target_resource_id         = azurerm_postgresql_flexible_server.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log {
    category = "PostgreSQLLogs"
  }

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

# =============================================================================
# Outputs
# =============================================================================

# Outputs
output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "api_endpoint" {
  value = "https://${azurerm_linux_web_app.api.default_hostname}"
}

output "web_endpoint" {
  value = azurerm_static_web_app.web.default_host_name
}

output "database_connection" {
  value     = "postgresql+asyncpg://${azurerm_postgresql_flexible_server.main.administrator_login}:${random_password.db_password.result}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${azurerm_postgresql_flexible_server_database.main.name}?sslmode=require"
  sensitive = true
}

output "redis_connection" {
  value     = "rediss://:${azurerm_redis_cache.main.primary_access_key}@${azurerm_redis_cache.main.hostname}:${azurerm_redis_cache.main.ssl_port}"
  sensitive = true
}

output "storage_connection" {
  value     = azurerm_storage_account.main.primary_connection_string
  sensitive = true
}

output "container_registry" {
  value = azurerm_container_registry.main.login_server
}

output "speech_key" {
  value     = azurerm_cognitive_account.speech.primary_access_key
  sensitive = true
}

output "openai_endpoint" {
  value = var.ai_provider == "azure_openai" ? azurerm_cognitive_account.openai[0].endpoint : null
}

output "openai_key" {
  value     = var.ai_provider == "azure_openai" ? azurerm_cognitive_account.openai[0].primary_access_key : null
  sensitive = true
}

output "application_insights_key" {
  value     = azurerm_application_insights.main.instrumentation_key
  sensitive = true
}
