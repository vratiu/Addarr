# IAM configuration and service account key generation for Addarr homelab daemon

resource "google_service_account" "addarr_bridge" {
  account_id   = var.service_account_id
  display_name = "Addarr Homelab Bridge Service Account"
  description  = "Service account used by local Addarr daemon to connect to Firebase Realtime Database"

  depends_on = [
    google_project_service.services["iam.googleapis.com"]
  ]
}

# Grant Firebase Realtime Database Admin role for message bridging
resource "google_project_iam_member" "rtdb_admin" {
  project = var.project_id
  role    = "roles/firebasedatabase.admin"
  member  = "serviceAccount:${google_service_account.addarr_bridge.email}"
}

# Generate service account private key
resource "google_service_account_key" "addarr_bridge_key" {
  service_account_id = google_service_account.addarr_bridge.name
}

# Export serviceAccountKey.json directly to repository root with secure file permissions
resource "local_sensitive_file" "service_account_key_json" {
  content         = base64decode(google_service_account_key.addarr_bridge_key.private_key)
  filename        = "${path.module}/../serviceAccountKey.json"
  file_permission = "0600"
}
