variable "project_id" {
  type        = string
  description = "The Google Cloud Project ID where Addarr cloud resources are deployed."
}

variable "region" {
  type        = string
  description = "Default Google Cloud region (must be a European region, e.g., europe-west1)."
  default     = "europe-west1"
}

variable "rtdb_location" {
  type        = string
  description = "Firebase Realtime Database location (europe-west1 for Europe)."
  default     = "europe-west1"
}

variable "app_display_name" {
  type        = string
  description = "Display name for the registered Firebase Web App."
  default     = "Addarr Telegram Mini App"
}

variable "service_account_id" {
  type        = string
  description = "Service account ID for the Addarr homelab bridge."
  default     = "addarr-homelab-bridge"
}
