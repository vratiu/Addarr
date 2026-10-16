# Core Google Cloud & Firebase Service APIs required for Addarr
locals {
  required_services = [
    "firebase.googleapis.com",
    "firebasedatabase.googleapis.com",
    "firebasehosting.googleapis.com",
    "identitytoolkit.googleapis.com",
    "iam.googleapis.com",
    "serviceusage.googleapis.com",
  ]
}

resource "google_project_service" "services" {
  for_each = toset(local.required_services)

  project = var.project_id
  service = each.key

  disable_on_destroy = false
}
