output "project_id" {
  value       = var.project_id
  description = "The Google Cloud Project ID."
}

output "database_url" {
  value       = google_firebase_database_instance.rtdb.database_url
  description = "The Firebase Realtime Database URL (located in Europe: europe-west1)."
}

output "hosting_url" {
  value       = "https://${google_firebase_hosting_site.default.site_id}.web.app"
  description = "The live Firebase Hosting URL for the Telegram Mini App."
}

output "service_account_email" {
  value       = google_service_account.addarr_bridge.email
  description = "The service account email provisioned for Addarr."
}

output "service_account_key_file" {
  value       = local_sensitive_file.service_account_key_json.filename
  description = "Path to the exported service account key for local Addarr daemon usage."
}

output "addarr_config_snippet" {
  value       = <<-EOT
    # Add or update this block in your Addarr config.yaml:
    miniapp:
      enable: true
      url: "https://${google_firebase_hosting_site.default.site_id}.web.app"
      databaseURL: "${google_firebase_database_instance.rtdb.database_url}"
      serviceAccountPath: "serviceAccountKey.json"
  EOT
  description = "YAML configuration snippet ready to paste into your Addarr config.yaml."
}
