# Design

## Context

Addarr currently operates as a self-hosted Python bot using `python-telegram-bot` in polling mode. It interacts with local instances of Sonarr and Radarr via REST API calls. To enable a responsive, visual Telegram Mini App without requiring public port forwarding, dynamic DNS, or third-party tunneling software inside the homelab, this design introduces an outbound message bridge using Google Cloud / Firebase (Hosting + Realtime Database).

See `proposal.md` for motivation and background.

## Goals / Non-Goals

**Goals:**
- **Zero Homelab Ingress:** Addarr connects strictly outbound to Google Cloud; no router ports are forwarded and no tunneling daemons are installed on the host.
- **Sub-Second Media Actions:** Fast search, instant poster previews, and 1-tap additions with pre-filled defaults.
- **Mutating Existing Titles:** Full support for updating quality profiles, monitored flags, and season-specific monitoring in Sonarr/Radarr.
- **Zero Cost Deployment:** Entire cloud architecture operates within the Google Cloud / Firebase always-free tier.
- **Tamper-Proof Authentication:** Cryptographic validation of Telegram `initData` against the bot token.

**Non-Goals:**
- Removing or deprecating existing conversational bot commands (`/start`, `/movie`, etc.); the Mini App complements them.
- Video playback, media streaming, or file downloads directly within Telegram.
- Multi-tenant cloud hosting of Sonarr/Radarr credentials; all local credentials remain strictly on the homelab host.

## Decisions

### 1. Transport Bridge: Firebase Realtime Database
* **Chosen Approach:** Use Firebase Realtime Database (RTDB) as a managed, serverless bi-directional message bus.
* **Mechanism:**
  - The Mini App pushes command payloads to `/users/{telegram_id}/requests/{req_id}`.
  - Addarr listens to this node via an outbound event stream (`firebase-admin` Python SDK).
  - Addarr executes the query against local Sonarr/Radarr, posts the result to `/users/{telegram_id}/responses/{req_id}`, and clears the request.
  - The Mini App receives the response via its real-time listener.
* **Alternatives Considered:**
  - *Cloudflare Tunnel / Ngrok:* Rejected due to the explicit constraint to avoid tunneling software in the homelab.
  - *Direct Cloud Run WebSocket Server:* Viable, but requires maintaining and deploying a custom container, and 24/7 idle connections can exceed Cloud Run's free tier CPU allocation. RTDB is 100% free on the Spark plan with zero server maintenance.

### 2. End-to-End Authentication & Authorization
* **Chosen Approach:** Telegram `initData` HMAC-SHA256 signature verification paired with Firebase Security Rules.
* **Mechanism:**
  - Upon launch, the Mini App passes its `initData` payload to a lightweight auth handler (or Cloud Function) which validates the hash using `HMAC-SHA256("WebAppData", bot_token)`.
  - Once validated, a Firebase Custom Auth Token is issued with `uid = telegram_user_id`.
  - RTDB Security Rules enforce that each user can only read and write to `/users/{auth.uid}/*`.
  - Addarr checks `auth.uid` against its configured `allowlist.txt` and `admin.txt` before fulfilling requests.
* **Alternatives Considered:**
  - *Unauthenticated public database nodes:* Rejected due to spam and unauthorized access vulnerabilities.
  - *Shared password entry inside Mini App:* Rejected as redundant, since Telegram already provides cryptographically signed user identity.

### 3. Frontend Architecture: Single-Page Application (SPA)
* **Chosen Approach:** React + Vite + Tailwind CSS with `@telegram-apps/sdk`.
* **Mechanism:** Compiled to static HTML/JS/CSS assets and deployed to Firebase Hosting (`firebase deploy`).
* **Key Components:**
  - `SearchTab`: Live search bar, debounce, poster card results, quick-add drawer.
  - `LibraryTab`: Grid view with filter pills (All, Downloaded, Missing, Unmonitored) and sorting (Title, Year, Added).
  - `DetailModal`: Quality profile dropdown, root folder selector, season monitoring checkboxes, and delete/search action triggers.
* **Alternatives Considered:**
  - *Server-rendered HTMX inside Addarr:* Requires exposing an HTTP server to the internet, which violates the no-tunnel constraint.

### 4. Backend Library Mutations in Addarr
* **Chosen Approach:** Extend `sonarr.py` and `radarr.py` with update functions:
  - `updateMovie(movieId, qualityProfileId, monitored)` via `PUT /api/v3/movie/{id}`.
  - `updateSeries(seriesId, qualityProfileId, monitored, seasons)` via `PUT /api/v3/series/{id}`.
  - `getLibrarySummary(app)` to return lightweight lists of movies/series with poster URLs, IDs, and statuses.

## Risks / Trade-offs

* **[Risk] Round-Trip Latency through Cloud Bus**  
  *Mitigation:* Firebase Realtime Database uses persistent WebSockets on both the client and Python sides. Message relay takes < 150ms. Local Sonarr/Radarr queries take ~50-100ms. Total round-trip is ~250ms, delivering a snappy native feel.
* **[Risk] Large Library Payload Size**  
  *Mitigation:* Large libraries (e.g., 2,000+ movies) could transfer megabytes if raw Sonarr JSON is sent. The Addarr bridge extracts only essential fields (`id`, `title`, `year`, `poster`, `profileId`, `monitored`, `status`) before writing to the database.
* **[Risk] Missing Service Account Credentials on Local Host**  
  *Mitigation:* If the `serviceAccountKey.json` is missing or disabled in `config.yaml`, Addarr logs a clear informative message and continues operating normal chat commands without crashing.

## Migration Plan

1. **Deploy Cloud Resources:** Deploy the static frontend to Firebase Hosting and configure RTDB rules.
2. **Update Addarr Configuration:** Add a `miniapp` block to `config.yaml` specifying `enable: true` and the path to `serviceAccountKey.json`.
3. **Run Addarr:** Addarr initializes the outbound listener asynchronously alongside the Telegram bot polling loop.
4. **Rollback:** Setting `miniapp.enable: false` disables all Mini App bridge operations, instantly restoring Addarr to its original pure-bot state.
