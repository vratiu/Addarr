# Design

## Context

Addarr's Telegram Mini App communicates with the home server over a Firebase Realtime Database bridge (`src/bridge.py` and `webapp/src/services/bridge.ts`). Currently, `App.tsx` maintains two independent top-level state variables: `activeTab` (`'search' | 'library'`) and `mediaType` (`'movie' | 'series'`). Both Radarr and Sonarr expose `/api/v3/calendar` REST endpoints via `commons.generateApiQuery`. See `proposal.md` for motivation and `specs/` for behavioral requirements.

## Goals / Non-Goals

**Goals:**
- Provide a clean, low-latency calendar query pipeline through `src/radarr.py`, `src/sonarr.py`, and `src/bridge.py` that returns pre-filtered, pre-grouped, and pre-sorted upcoming releases (up to 60 days / 20 entries).
- Extend the Mini App UI (`Navbar.tsx`, `App.tsx`, `CalendarTab.tsx`) so switching `mediaType` (`Movies | Series`) while on the `Calendar` tab stays on the `Calendar` tab and loads the corresponding feed.
- Compute accurate local calendar day offsets in the frontend to display relative day indicators for releases `< 14` days away.

**Non-Goals:**
- Full monthly grid/calendar matrix UI (the feature is explicitly designed as a vertical chronological list).
- Modifying release dates or episode air dates in Sonarr/Radarr.
- Including theatrical (`inCinemas`) or physical (`physicalRelease`) movie dates when a movie has no upcoming digital release within the 60-day window.

## Decisions

### 1. Backend Filtering & Grouping vs. Frontend Raw Processing
- **Decision**: Perform the 60-day window query, Radarr `digitalRelease` filtering, Sonarr same-day episode grouping, chronological sorting, and 20-item slicing on the Python backend (`src/radarr.py` and `src/sonarr.py`) before writing to Firebase RTDB.
- **Rationale**: Firebase RTDB acts as a message relay between the homelab and the Telegram WebApp. Minimizing payload size over RTDB reduces latency and bandwidth, especially when a user tracks many series or when a streaming show drops an entire season on one day.
- **Alternatives considered**: Returning raw `/api/v3/calendar` responses over RTDB and filtering in React. Rejected because raw Sonarr calendar objects with `includeSeries=true` can be large and contain unnecessary metadata.

### 2. Radarr Digital Release Filtering Strategy
- **Decision**: Call Radarr's `GET /api/v3/calendar` with `start=<today_iso>`, `end=<today_plus_60d_iso>`, and `unmonitored=false`. For each returned movie, parse `movie.get("digitalRelease")` and retain only movies where `digitalRelease` falls within `[today, today + 60 days]`. Sort ascending by `digitalRelease` and slice `[:20]`.
- **Rationale**: Radarr's `/api/v3/calendar` matches a movie if *any* of `inCinemas`, `digitalRelease`, or `physicalRelease` falls in `[start, end]`. Filtering specifically on `digitalRelease` guarantees that only Digital format releases are surfaced and that the displayed date is always the digital release date.

### 3. Sonarr Same-Day Episode Grouping Strategy
- **Decision**: Call Sonarr's `GET /api/v3/calendar` with `start=<today_iso>`, `end=<today_plus_60d_iso>`, `unmonitored=false`, and `includeSeries=true`. Group episodes by `(seriesId, seasonNumber, airDate)`.
  - If a group has 1 episode: return `seasonNumber`, `episodeNumber`, and `episodeTitle` (e.g., `S02E04 • Woe's Hollow`).
  - If a group has multiple episodes on the same day: return `seasonNumber`, `episodeNumber` (first), `endEpisodeNumber` (last), `episodeCount`, and a combined label/summary (e.g., `S02E01-E08 (8 episodes)`).
  - Sort groups chronologically by release date (`airDateUtc` / `airDate`) and slice `[:20]`.
- **Rationale**: Prevents a single binge-released season (e.g., 8–10 episodes dropping on the same day) from consuming half of the 20-entry cap while still showing exact episode numbers for weekly releases.

### 4. Relative Day Calculation (`< 14` days)
- **Decision**: Compare the calendar date (normalized to midnight in the user's local timezone / calendar day) against today's local midnight:
  - `diffDays = Math.round((releaseMidnight - todayMidnight) / 86400000)`
  - When `0 <= diffDays < 14`, append relative text beside the formatted date:
    - `0` -> `(today)`
    - `1` -> `(tomorrow)`
    - `2..13` -> `(in X days)`
  - When `diffDays >= 14`, show only the formatted date (e.g., `Nov 15, 2026`).
- **Rationale**: Using calendar-day boundaries avoids off-by-one hour rounding issues caused by time-of-day differences between UTC timestamps and local time.

### 5. Separate Bridge Actions Following Library Authorization Rules
- **Decision**: Add `get_calendar_movies` and `get_calendar_series` actions in `src/bridge.py`, applying the same `_requires_admin` checks as `get_library_movies` (`radarr.adminRestrictions`) and `get_library_series` (`sonarr.adminRestrictions`).
- **Rationale**: Keeps authorization consistent with existing read operations per media service and matches the `mediaType` toggle in the UI.

## Risks / Trade-offs

- **[Risk] Sonarr/Radarr date strings vary between date-only (`YYYY-MM-DD`) and full ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`)** → **Mitigation**: Normalize date strings to `YYYY-MM-DD` (and retain full ISO timestamp where available) in `radarr.py` and `sonarr.py` so both backend range checks and frontend date parsing behave deterministically across timezones.
- **[Risk] Poster URLs in Sonarr `includeSeries=true` calendar payload may be nested under `series.images`** → **Mitigation**: Reuse the same poster extraction logic from `get_library_summary()` (checking `images` with `coverType == "poster"` for `remoteUrl` or `url`, falling back to `remotePoster`).
