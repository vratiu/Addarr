# Addarr OpenTofu Infrastructure

This directory contains OpenTofu (IaC) configuration for deploying Addarr's cloud message relay (Firebase Realtime Database), Web App frontend (Firebase Hosting), and service account credentials onto Google Cloud under the **Free Tier** in a European region (`europe-west1`).

---

## Quickstart

### 1. Prerequisites & Authentication

> [!IMPORTANT]
> **Mandatory Quota Project Requirement:**  
> The Firebase Realtime Database API (`firebasedatabase.googleapis.com`) requires an active quota project when authenticating via local Application Default Credentials (ADC). You **must** run step 4 below before running `tofu apply`.

```bash
# 1. Authenticate gcloud CLI
gcloud auth login

# 2. Set your target project
gcloud config set project <your-actual-project-id>

# 3. Authenticate Application Default Credentials (ADC)
gcloud auth application-default login

# 4. Set the quota project for ADC (REQUIRED)
gcloud auth application-default set-quota-project <your-actual-project-id>

# 5. Log in to Firebase CLI
firebase login
```

---

### 2. Configuration & Deployment

1. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` and specify your actual GCP `project_id`:
   ```hcl
   project_id = "your-actual-project-id"

   # European Region (Default: europe-west1 / Belgium)
   region        = "europe-west1"
   rtdb_location = "europe-west1"
   ```

3. Initialize and deploy:
   ```bash
   tofu init
   tofu apply
   ```

---

### 3. Generated Files

Upon successful apply, OpenTofu automatically generates:
- `../serviceAccountKey.json`: Dedicated credential file for the local Addarr daemon (chmod 0600).
- `../webapp/.env.production`: Live production API keys and database URL for the Mini App.
- `../webapp/firebase.json`: Hosting configuration for single-page app routing.

For complete documentation, see [`docs/OPENTOFU_DEPLOYMENT.md`](../docs/OPENTOFU_DEPLOYMENT.md).
