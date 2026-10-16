# Firebase Project, Web App registration, and Realtime Database in Europe

resource "google_firebase_project" "default" {
  provider = google-beta
  project  = var.project_id

  depends_on = [
    google_project_service.services["firebase.googleapis.com"]
  ]
}

# Realtime Database instance provisioned in Europe (europe-west1)
resource "google_firebase_database_instance" "rtdb" {
  provider    = google-beta
  project     = var.project_id
  region      = var.rtdb_location
  instance_id = "${var.project_id}-default-rtdb"
  type        = "DEFAULT_DATABASE"

  depends_on = [
    google_firebase_project.default,
    google_project_service.services["firebasedatabase.googleapis.com"]
  ]
}

# Apply Realtime Database Security Rules from firebase/database.rules.json
resource "terraform_data" "rtdb_rules" {
  triggers_replace = [
    filesha256("${path.module}/../firebase/database.rules.json")
  ]

  provisioner "local-exec" {
    command = <<-EOT
      echo "Applying Firebase Realtime Database rules..."
      TOKEN=$(gcloud auth print-access-token --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/firebase.database,https://www.googleapis.com/auth/userinfo.email 2>/dev/null || gcloud auth print-access-token 2>/dev/null || true)
      if [ -n "$TOKEN" ] && curl -s -f -X PUT \
          -H "Authorization: Bearer $TOKEN" \
          -H "Content-Type: application/json" \
          --data-binary "@${path.module}/../firebase/database.rules.json" \
          "${google_firebase_database_instance.rtdb.database_url}/.settings/rules.json" > /dev/null; then
        echo "Rules applied successfully via Firebase REST API."
      elif command -v firebase >/dev/null 2>&1; then
        firebase deploy --only database --project "${var.project_id}" || true
      else
        echo "Notice: Neither gcloud token nor firebase CLI was available to auto-push rules."
        echo "Rules can also be deployed with: firebase deploy --only database --project ${var.project_id}"
      fi
    EOT
  }

  depends_on = [
    google_firebase_database_instance.rtdb
  ]
}

# Register the Web App under Firebase to obtain API keys and configuration
resource "google_firebase_web_app" "default" {
  provider     = google-beta
  project      = var.project_id
  display_name = var.app_display_name

  depends_on = [
    google_firebase_project.default
  ]
}

data "google_firebase_web_app_config" "default" {
  provider   = google-beta
  project    = var.project_id
  web_app_id = google_firebase_web_app.default.app_id
}
