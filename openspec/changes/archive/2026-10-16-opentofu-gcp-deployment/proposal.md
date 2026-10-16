# Proposal

## Why

Setting up the Google Cloud and Firebase infrastructure for the Addarr Telegram Mini App currently requires manual navigation through multiple Firebase and GCP console menus, manual database creation, manual security rule pasting, and manual service account key extraction. 

Automating this with OpenTofu (IaC) provides a reproducible, one-command deployment that provisions the cloud relay, exports the homelab credentials, builds and publishes the Mini App frontend to Firebase Hosting, and enforces GCP/Firebase Free Tier guardrails in a European region (`europe-west1`).

## What Changes

- Add OpenTofu configuration under `tofu/` targeting Google Cloud and Firebase.
- Automate provisioning of GCP services, Firebase project, Realtime Database (RTDB) in `europe-west1`, and database security rules.
- Automate creation and least-privilege IAM binding of the Addarr homelab service account, writing `serviceAccountKey.json` directly for the local daemon.
- Automate registration of the Firebase Web App and generate `webapp/.env.production` containing the live credentials.
- Automate the end-to-end frontend build (`npm run build`) and deployment to Firebase Hosting via OpenTofu.
- Configure Free Tier guardrails to ensure usage strictly adheres to Google Cloud Always Free and Firebase Spark plan limits with zero recurring costs.
- Provide comprehensive deployment and rollback documentation for European homelab operators.

## Capabilities

### New Capabilities

- `cloud-infrastructure/opentofu-provisioning`: Automated, reproducible provisioning of Google Cloud and Firebase infrastructure (RTDB message broker, security rules, service account credentials, and webapp hosting) using OpenTofu within Free Tier limits.

### Modified Capabilities

None. Existing system requirements for `telegram-mini-app/bridge` and `telegram-mini-app/client` remain unchanged.

## Impact

- **New Files**: Dedicated `tofu/` directory containing OpenTofu configs (`main.tf`, `variables.tf`, `services.tf`, `firebase.tf`, `iam.tf`, `hosting.tf`, `outputs.tf`).
- **Generated Artifacts**: Creates `serviceAccountKey.json` in root (git-ignored) and `webapp/.env.production`.
- **Runtime Impact**: Zero breaking changes to existing Addarr homelab daemon or bot commands.
- **Dependencies**: Requires OpenTofu (or Terraform), Node.js (for webapp build), and Google Cloud CLI / Firebase CLI installed on the operator's machine.
