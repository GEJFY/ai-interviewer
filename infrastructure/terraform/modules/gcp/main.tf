# GCP Infrastructure Module for AI Interview Tool

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.14"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.14"
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

variable "region" {
  type    = string
  default = "asia-northeast1"
}

variable "labels" {
  type = map(string)
}

variable "suffix" {
  type = string
}

variable "ai_provider" {
  type = string
}

variable "project_id" {
  type    = string
  default = ""
}

data "google_project" "current" {}

locals {
  project_id = var.project_id != "" ? var.project_id : data.google_project.current.project_id
  gcp_labels = {
    for k, v in var.labels : lower(replace(k, "/[^a-z0-9_-]/", "_")) => lower(replace(v, "/[^a-z0-9_-]/", "_"))
  }
}

# Enable APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "sqladmin.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "speech.googleapis.com",
    "translate.googleapis.com",
    "redis.googleapis.com",
    "servicenetworking.googleapis.com",
    "cloudbuild.googleapis.com"
  ])

  project = local.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}

# VPC Network
resource "google_compute_network" "main" {
  name                    = "${var.resource_prefix}-vpc"
  auto_create_subnetworks = false
  project                 = local.project_id

  depends_on = [google_project_service.apis["compute.googleapis.com"]]
}

resource "google_compute_subnetwork" "main" {
  name          = "${var.resource_prefix}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.main.id
  project       = local.project_id

  secondary_ip_range {
    range_name    = "services-range"
    ip_cidr_range = "10.1.0.0/16"
  }

  secondary_ip_range {
    range_name    = "pod-range"
    ip_cidr_range = "10.2.0.0/16"
  }
}

# Private Services Access for Cloud SQL
resource "google_compute_global_address" "private_ip" {
  name          = "${var.resource_prefix}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
  project       = local.project_id
}

resource "google_service_networking_connection" "private_vpc" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip.name]

  depends_on = [google_project_service.apis["servicenetworking.googleapis.com"]]
}

# Cloud SQL PostgreSQL
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "${var.resource_prefix}-db-password"
  project   = local.project_id

  replication {
    auto {}
  }

  labels = local.gcp_labels

  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_sql_database_instance" "main" {
  name             = "${var.resource_prefix}-db-${var.suffix}"
  database_version = "POSTGRES_16"
  region           = var.region
  project          = local.project_id

  deletion_protection = var.environment == "prod"

  settings {
    tier              = var.environment == "prod" ? "db-custom-4-16384" : "db-f1-micro"
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_size         = 20
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.main.id
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = var.environment == "prod"
      start_time                     = "02:00"
      backup_retention_settings {
        retained_backups = var.environment == "prod" ? 35 : 7
      }
    }

    database_flags {
      name  = "cloudsql.enable_pgvector"
      value = "on"
    }

    insights_config {
      query_insights_enabled  = var.environment == "prod"
      record_application_tags = true
      record_client_address   = true
    }
  }

  depends_on = [
    google_project_service.apis["sqladmin.googleapis.com"],
    google_service_networking_connection.private_vpc
  ]
}

resource "google_sql_database" "main" {
  name     = "aiinterviewer"
  instance = google_sql_database_instance.main.name
  project  = local.project_id
}

resource "google_sql_user" "main" {
  name     = "aiinterviewer"
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
  project  = local.project_id
}

# Memorystore Redis
resource "google_redis_instance" "main" {
  name               = "${var.resource_prefix}-redis"
  tier               = var.environment == "prod" ? "STANDARD_HA" : "BASIC"
  memory_size_gb     = var.environment == "prod" ? 4 : 1
  region             = var.region
  authorized_network = google_compute_network.main.id
  redis_version      = "REDIS_7_2"
  project            = local.project_id

  labels = local.gcp_labels

  depends_on = [google_project_service.apis["redis.googleapis.com"]]
}

# Cloud Storage
resource "google_storage_bucket" "main" {
  name          = "${var.resource_prefix}-storage-${var.suffix}"
  location      = var.region
  project       = local.project_id
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  labels = local.gcp_labels
}

# Artifact Registry
resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = "${var.resource_prefix}-repo"
  format        = "DOCKER"
  project       = local.project_id

  labels = local.gcp_labels

  depends_on = [google_project_service.apis["artifactregistry.googleapis.com"]]
}

# Service Account for Cloud Run
resource "google_service_account" "cloudrun" {
  account_id   = "${var.resource_prefix}-cloudrun"
  display_name = "Cloud Run Service Account"
  project      = local.project_id
}

resource "google_project_iam_member" "cloudrun_sql" {
  project = local.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_project_iam_member" "cloudrun_storage" {
  project = local.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_project_iam_member" "cloudrun_secretmanager" {
  project = local.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_project_iam_member" "cloudrun_aiplatform" {
  count   = var.ai_provider == "gcp_vertex" ? 1 : 0
  project = local.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_project_iam_member" "cloudrun_speech" {
  project = local.project_id
  role    = "roles/speech.client"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "api" {
  name     = "${var.resource_prefix}-api"
  location = var.region
  project  = local.project_id
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloudrun.email

    scaling {
      min_instance_count = var.environment == "prod" ? 2 : 0
      max_instance_count = var.environment == "prod" ? 10 : 2
    }

    vpc_access {
      network_interfaces {
        network    = google_compute_network.main.name
        subnetwork = google_compute_subnetwork.main.name
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${local.project_id}/${google_artifact_registry_repository.main.repository_id}/api:latest"

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = var.environment == "prod" ? "2" : "1"
          memory = var.environment == "prod" ? "2Gi" : "512Mi"
        }
      }

      env {
        name  = "DATABASE_URL"
        value = "postgresql+asyncpg://${google_sql_user.main.name}:${random_password.db_password.result}@${google_sql_database_instance.main.private_ip_address}:5432/${google_sql_database.main.name}"
      }

      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.main.host}:${google_redis_instance.main.port}"
      }

      env {
        name  = "GCS_BUCKET"
        value = google_storage_bucket.main.name
      }

      env {
        name  = "AI_PROVIDER"
        value = var.ai_provider
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = local.project_id
      }

      startup_probe {
        http_get {
          path = "/api/v1/health"
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/api/v1/health"
        }
        timeout_seconds = 3
        period_seconds  = 30
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  labels = local.gcp_labels

  depends_on = [
    google_project_service.apis["run.googleapis.com"],
    google_sql_database_instance.main,
    google_redis_instance.main
  ]
}

# Allow unauthenticated access (with API-level auth)
resource "google_cloud_run_v2_service_iam_member" "public" {
  location = google_cloud_run_v2_service.api.location
  project  = local.project_id
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Firebase Hosting for Frontend (optional)
resource "google_firebase_hosting_site" "web" {
  provider = google-beta
  project  = local.project_id
  site_id  = "${var.resource_prefix}-web-${var.suffix}"
}

# Outputs
output "project_id" {
  value = local.project_id
}

output "api_endpoint" {
  value = google_cloud_run_v2_service.api.uri
}

output "database_connection" {
  value     = "postgresql+asyncpg://${google_sql_user.main.name}:${random_password.db_password.result}@${google_sql_database_instance.main.private_ip_address}:5432/${google_sql_database.main.name}"
  sensitive = true
}

output "redis_connection" {
  value = "redis://${google_redis_instance.main.host}:${google_redis_instance.main.port}"
}

output "storage_bucket" {
  value = google_storage_bucket.main.name
}

output "artifact_registry" {
  value = "${var.region}-docker.pkg.dev/${local.project_id}/${google_artifact_registry_repository.main.repository_id}"
}

output "service_account" {
  value = google_service_account.cloudrun.email
}
