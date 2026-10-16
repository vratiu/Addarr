# Spec Delta

## Purpose

Automates the provisioning and configuration of Google Cloud and Firebase infrastructure required for Addarr's cloud relay and Mini App frontend using OpenTofu within Free Tier limits.

## ADDED Requirements

### Requirement: Automated Cloud Relay Provisioning
The infrastructure code SHALL provision Google Cloud services, a Firebase project, and a Firebase Realtime Database located in a European region (`europe-west1`) with production security rules.

#### Scenario: Successful infrastructure creation
- **WHEN** the operator runs OpenTofu apply with a valid European GCP project ID
- **THEN** the Firebase project, `europe-west1` Realtime Database instance, and database security rules are provisioned automatically

#### Scenario: Security rules application
- **WHEN** the Realtime Database is created
- **THEN** security rules restrict access so that users can only read and write to their own request and response nodes

### Requirement: Homelab Credential Generation
The infrastructure code SHALL create a dedicated service account with minimal required roles and export the service account key for local Addarr daemon usage.

#### Scenario: Service account key export
- **WHEN** OpenTofu applies the IAM and service account resources
- **THEN** a `serviceAccountKey.json` credential file is generated locally for the Addarr daemon and marked as git-ignored

### Requirement: Automated Frontend Build and Hosting Release
The infrastructure code SHALL generate the client environment configuration, build the production webapp bundle, and release it to Firebase Hosting.

#### Scenario: End-to-end frontend release
- **WHEN** OpenTofu executes the hosting and build steps
- **THEN** `webapp/.env.production` is populated with the provisioned database URL and Web API key, `npm run build` is executed, and the bundle is published to the Firebase Hosting site

#### Scenario: Frontend asset rebuild on source change
- **WHEN** files within `webapp/src` or `webapp/package.json` change and OpenTofu apply is run
- **THEN** OpenTofu detects the hash change, rebuilds the distribution assets, and deploys a new hosting release

### Requirement: Free Tier and Region Enforcement
The infrastructure code SHALL restrict all provisioned cloud resources to Google Cloud Always Free and Firebase Spark plan specifications in European regions to prevent recurring operational costs.

#### Scenario: Free tier resource verification
- **WHEN** the infrastructure is applied
- **THEN** all resources operate under zero-cost free-tier specifications without auto-scaling paid instances
