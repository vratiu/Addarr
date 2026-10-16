# Proposal

## Why

Adding media to Sonarr and Radarr via Addarr currently requires stepping through a multi-message conversational flow in Telegram chat, browsing large libraries produces unformatted text dumps, and there is no way to view or edit preferences (such as quality profiles or season monitoring) for existing titles.

Introducing a Telegram Mini App (TMA) provides an interactive, visual media interface right inside Telegram with instant search, poster walls, and single-tap configuration, while keeping the homelab completely private and behind NAT using an outbound-only real-time bridge.

## What Changes

- **Telegram Mini App Frontend**: A responsive, lightweight single-page web app launched directly from Telegram via an inline or menu button.
- **Fast Media Search & Add**: Instant search with poster previews and a streamlined single-screen modal to select root folder, quality profile, and monitor options in 1–2 taps.
- **Visual Library Browser**: Filterable and searchable poster grid showing downloaded status, missing status, and monitored flags for movies and series.
- **Library Preference Management**: Capability to view and modify stored movie/series preferences (switch quality profile, toggle monitored status, customize monitored seasons/episodes in Sonarr).
- **Outbound-Only Real-time Bridge**: An event listener within Addarr that connects outbound to a cloud sync relay (e.g., Firebase Realtime Database) so no ports are forwarded and no inbound tunnels are required in the homelab.
- **End-to-End Cryptographic Security**: Authentication via Telegram `initData` signature validation against the bot token, ensuring only authorized Telegram users can read or trigger commands.

## Capabilities

### New Capabilities
- `telegram-mini-app/client`: The Telegram Mini App web frontend rendering search, poster grids, single-step addition modals, and preference editors inside Telegram webviews.
- `telegram-mini-app/bridge`: The outbound-only real-time transport bridge connecting Addarr behind the router to Google Cloud/Firebase with end-to-end authentication.
- `media-management/library-mutations`: Inspection and mutation of existing media records in Sonarr and Radarr (updating quality profiles, toggling monitored state, configuring season monitoring).

### Modified Capabilities
<!-- No existing specs in the project -->

## Impact

- **Addarr Core (`src/`)**: Addition of a bridge listener module running alongside the existing `Application` event loop in Python; additions to `sonarr.py` and `radarr.py` to support updating series/movie settings (`PUT` endpoints).
- **Configuration (`config.yaml`)**: New configuration block for Mini App and bridge settings (Firebase project credentials, enabled status, Mini App URL).
- **Dependencies (`requirements.txt`)**: Inclusion of Firebase/realtime bridge dependencies (such as `firebase-admin` or lightweight SSE/WSS client).
- **Hosting / Cloud**: Static hosting setup for the Mini App (Firebase Hosting) and database security rules.
