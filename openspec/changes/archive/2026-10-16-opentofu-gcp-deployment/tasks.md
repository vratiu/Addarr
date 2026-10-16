# Tasks

## 1. OpenTofu Scaffolding and Provider Setup

- [x] 1.1 Create `tofu/` directory with `main.tf`, `variables.tf`, and `terraform.tfvars.example` configured for `hashicorp/google` and `hashicorp/google-beta` providers with European region `europe-west1` as default and verify syntax with `tofu fmt -check`.
- [x] 1.2 Implement `tofu/services.tf` defining the necessary Google Cloud Service APIs (`firebase.googleapis.com`, `firebasedatabase.googleapis.com`, `firebasehosting.googleapis.com`) and verify plan structure.

## 2. Firebase Infrastructure and IAM Configuration

- [x] 2.1 Implement `tofu/firebase.tf` provisioning the `google_firebase_project`, `google_firebase_web_app`, `google_firebase_database_instance` in `europe-west1`, and applying security rules from `firebase/database.rules.json`, verifying resource definitions with `tofu validate`.
- [x] 2.2 Implement `tofu/iam.tf` creating the dedicated Addarr service account with least-privilege roles, generating a private key written to `serviceAccountKey.json` with `0600` permissions, and verify key export logic.

## 3. Frontend Build and Firebase Hosting Release

- [x] 3.1 Implement `tofu/hosting.tf` using `terraform_data` to generate `webapp/.env.production` from provisioned outputs, execute `npm run build` upon asset hash changes, and release to Firebase Hosting.
- [x] 3.2 Implement `tofu/outputs.tf` outputting `hosting_url`, `database_url`, `project_id`, and homelab configuration snippets, verifying output definitions with `tofu validate`.

## 4. Documentation, Safety Guardrails, and Verification

- [x] 4.1 Add `docs/OPENTOFU_DEPLOYMENT.md` detailing prerequisites, European region defaults, step-by-step deployment, Free Tier budget safety tips, and teardown instructions.
- [x] 4.2 Update `.gitignore` to protect OpenTofu local state (`*.tfstate*`, `.terraform/`) and generated credentials, verifying repository hygiene and formatting.

## Workflow follow-up

- Archive the change after the project's review requirements are satisfied.
- Verify the archived result.
