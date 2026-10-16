# Design

## Context

Addarr uses a zero-tunnel bridge architecture where a cloud-based message broker (Firebase Realtime Database) relays messages between external clients (Telegram Mini App) and the homelab daemon running inside a home network. See `proposal.md` for motivation.

The deployment of this cloud layer was previously documented in `docs/MINIAPP_SETUP.md` as a multi-step manual process. This design formalizes the implementation of an Infrastructure as Code (IaC) configuration using **OpenTofu** that provisions and manages the cloud relay, client hosting, and access credentials.

## Goals / Non-Goals

**Goals:**
- Provide a clean OpenTofu configuration under `tofu/` targeting Google Cloud and Firebase.
- Default all provisioned infrastructure to European regions (`europe-west1`) for optimal latency and compliance.
- Enforce strict adherence to Google Cloud Always Free and Firebase Spark plan capabilities (guaranteed $0 operational cost).
- Automate the end-to-end client build and release: generate `webapp/.env.production`, run Vite production build, and publish to Firebase Hosting.
- Automate local export of `serviceAccountKey.json` directly into the Addarr root with restrictive file permissions.

**Non-Goals:**
- Deploying the Addarr Python daemon to GCP (the daemon remains local in the homelab).
- Multi-environment staging/dev pipelines (focused exclusively on production for now).
- Deploying Always-On paid compute (e.g. Cloud Run instances or GKE clusters).

## Decisions

### 1. OpenTofu with Google / Google-Beta Providers
- **Decision:** Use OpenTofu with `hashicorp/google` and `hashicorp/google-beta` providers.
- **Rationale:** Native support for `google_firebase_project`, `google_firebase_database_instance`, and `google_firebase_web_app`.
- **Alternatives Considered:** 
  - *Custom shell scripts with `firebase-tools`:* Imperative, fragile, lacks state tracking and drift detection.
  - *Pulumi:* Requires Node.js/Python runtime for IaC execution rather than standard declarative HCL.

### 2. European Region Configuration (`europe-west1`)
- **Decision:** Pin RTDB and GCP region variables to `europe-west1` (Belgium).
- **Rationale:** The operator and primary users are based in Europe. `europe-west1` is the European region supporting Firebase Realtime Database and minimizes round-trip latency to the homelab bridge.
- **Alternatives Considered:** `us-central1` (default for many GCP templates, but introduces unnecessary transatlantic latency).

### 3. Spark Plan Zero-Cost Architecture (No Mandatory Cloud Functions)
- **Decision:** Rely on Firebase Realtime Database + Firebase Hosting without mandating Cloud Functions.
- **Rationale:** Cloud Functions require the Blaze (billing account attached) plan. On the Spark (Free) plan, RTDB offers 1 GB storage, 10 GB/month transfer, and 100 concurrent connections 100% free without credit card requirements. Addarr's backend already enforces user authorization locally against `admin.txt` and `allowlist.txt` in `src/bridge.py`.
- **Alternatives Considered:** 2nd Gen Cloud Functions for auth proxying (would require linking a credit card, violating the pure zero-commitment free-tier goal).

### 4. Full Deployment Lifecycle using `terraform_data`
- **Decision:** Use `terraform_data` to detect source file changes (`webapp/src/**`, `webapp/package.json`), generate `webapp/.env.production`, execute `npm run build`, and publish the release.
- **Rationale:** Fulfills the "deploy everything" requirement in one `tofu apply` command without requiring a separate CI/CD pipeline.
- **Alternatives Considered:** Requiring the user to run manual build and deployment scripts after `tofu apply`.

### 5. Local Credential Delivery for Homelab
- **Decision:** Generate a `google_service_account_key` in Tofu and write it directly to `${path.root}/../serviceAccountKey.json` with permissions `0600`.
- **Rationale:** The local Addarr daemon requires this file to authenticate with Firebase Admin SDK. Generating it automatically eliminates error-prone manual console downloads.

## Risks / Trade-offs

- **[Risk: Spark Plan Quota Exhaustion]** → **Mitigation:** Addarr requests are 5–20 KB JSON payloads. A typical user sending 100 requests daily consumes ~50 MB/month, which is 0.5% of the 10 GB/month free transfer quota.
- **[Risk: Storing Private Key in OpenTofu State]** → **Mitigation:** Service account private keys stored in state are standard in Terraform; documentation will instruct users to keep their local state file secure and git-ignored.
- **[Risk: Node / NPM dependency on operator machine]** → **Mitigation:** The build step checks for Node.js availability and outputs clear error diagnostics if `npm` is missing.

## Migration Plan

1. **Prerequisites:** Install OpenTofu (`brew install opentofu`) and Google Cloud CLI (`gcloud`).
2. **Execution:** Operator authenticates (`gcloud auth application-default login`), runs `tofu init` and `tofu apply` with their GCP project ID.
3. **Homelab Linking:** `serviceAccountKey.json` is automatically placed in the project root. Addarr config (`config.yaml`) is updated with the output `databaseURL` and `miniapp.url`.
4. **Rollback Strategy:** Running `tofu destroy` cleanly deletes all cloud resources without affecting the homelab Addarr configuration or media libraries.
