# Proposal

## Why

Users can currently search for media and browse their existing library in the Telegram Mini App, but have no visibility into when monitored movies will be released digitally or when upcoming series episodes will air. Adding a dedicated "Calendar" tab backed by Radarr and Sonarr's calendar data lets users see upcoming releases over the next 60 days directly inside the Mini App.

## What Changes

- Add a new **Calendar** tab to the Telegram Mini App navigation bar alongside **Search & Add** and **My Library**.
- Preserve the active tab (`search`, `library`, or `calendar`) when toggling the global **Movies | Series** switcher in the header so switching media types on the Calendar tab transitions directly between movie and series calendars without resetting to Search.
- Query Radarr's calendar endpoint (`/api/v3/calendar`) for upcoming monitored movies and filter specifically for **Digital format** releases (`digitalRelease`) occurring within the next 60 days, sorted chronologically and capped at 20 entries.
- Query Sonarr's calendar endpoint (`/api/v3/calendar` with `includeSeries=true`) for upcoming monitored episodes airing within the next 60 days, grouping multiple episodes of the same series airing on the same date into a single list entry, sorted chronologically and capped at 20 entries.
- Display each calendar entry in a list with poster art, title, release/episode metadata, and release date, including a calculated relative day indicator (e.g., `(today)`, `(tomorrow)`, `(in 3 days)`) whenever the release date is less than 14 days away (`< 14` days).
- Expose `get_calendar_movies` and `get_calendar_series` actions in the Addarr Firebase RTDB bridge (`src/bridge.py`) and frontend `BridgeService` (`webapp/src/services/bridge.ts`).

## Capabilities

### New Capabilities
- `media-management/release-calendar`: Querying, filtering, and grouping upcoming digital movie releases from Radarr and upcoming series episode airings from Sonarr within a 60-day window (up to 20 entries).

### Modified Capabilities
- `telegram-mini-app/client`: Adding the Calendar tab UI, preserving tab state across the Movies/Series toggle, and rendering release dates with `< 14` day relative day calculations.
- `telegram-mini-app/bridge`: Dispatching and authorizing `get_calendar_movies` and `get_calendar_series` commands over the real-time bridge.

## Impact

- **Backend (`src/radarr.py`, `src/sonarr.py`, `src/bridge.py`)**:
  - New calendar query helpers in `src/radarr.py` (`get_calendar_movies`) and `src/sonarr.py` (`get_calendar_series`).
  - New bridge actions `get_calendar_movies` and `get_calendar_series` in `src/bridge.py` (including admin restriction checks matching library read actions).
- **Frontend (`webapp/src/`)**:
  - Updated tab union type and navigation bar in `webapp/src/App.tsx` and `webapp/src/components/Navbar.tsx`.
  - New `CalendarItem` type in `webapp/src/types.ts` and `getCalendar(type)` method in `webapp/src/services/bridge.ts`.
  - New `webapp/src/components/CalendarTab.tsx` component implementing the list view, `< 14` days relative date calculation, and empty/loading states.
- **Tests (`tests/`)**:
  - Unit tests covering Radarr digital release calendar filtering, Sonarr same-day episode grouping, and bridge action dispatch/authorization.
