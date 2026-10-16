# telegram-mini-app/bridge Specification

## Purpose
Provides a secure, outbound-only real-time transport bridge connecting Addarr behind local NAT to external cloud relays without opening firewall ports.

## Requirements

### Requirement: Outbound Event Connection
The bridge SHALL establish and maintain an outbound connection to the cloud message broker to receive commands.

#### Scenario: Startup connection establishment
- **WHEN** Addarr initializes with the bridge module enabled
- **THEN** the bridge establishes an outbound connection to the cloud relay and listens for incoming requests

### Requirement: Authenticate Telegram Requests
The bridge and cloud relay SHALL verify the authenticity of client requests using Telegram `initData` cryptographic signatures.

#### Scenario: Valid Telegram signature
- **WHEN** a client request arrives containing valid `initData` signed with the bot token
- **THEN** the request is accepted and authenticated to the sender's Telegram user ID

#### Scenario: Invalid or tampered signature
- **WHEN** a request arrives with an invalid hash or mismatched user ID
- **THEN** the request is rejected immediately with an authentication error

### Requirement: Request Authorization
The bridge SHALL ensure requests originate from authorized Telegram users specified in Addarr's access lists.

#### Scenario: User in allowlist
- **WHEN** an authenticated user whose ID is present in the allowlist issues a command
- **THEN** the bridge dispatches the command to the local media service

#### Scenario: Unauthorized user
- **WHEN** an authenticated user whose ID is not permitted issues a command
- **THEN** the bridge refuses execution and logs the unauthorized attempt

### Requirement: Command Dispatch and Response Handling
The bridge SHALL execute dispatched actions locally against media services and return responses to the cloud broker.

#### Scenario: Command execution round-trip
- **WHEN** a valid `search_movie` command is received by the bridge
- **THEN** the bridge executes the query against local Radarr and writes the formatted result payload back to the response queue
