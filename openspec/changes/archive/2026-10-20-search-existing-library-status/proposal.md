# Proposal

## Why

When searching for a movie or series in the Telegram Mini App, results that already exist in Radarr or Sonarr currently display the same `+` (Add) button as unadded titles and open the Quick Add modal. Users cannot easily distinguish which search results are already in their library or directly modify their quality profile, monitoring settings, or removal options without switching tabs and searching again in "My Library".

## What Changes

- Enrich `radarr.giveTitles()` and `sonarr.giveTitles()` search formatting so existing library metadata returned by Radarr/Sonarr lookup endpoints (`libraryId` when internal `id > 0`, `inLibrary`, `qualityProfileId`, `monitored`, `status`, `hasFile`, `sizeOnDisk`, `episodeCount`, `episodeFileCount`, and `seasons`) is preserved alongside the external `id` (`tmdbId` / `tvdbId`).
- Update the horizontal search result row in the Mini App `SearchTab` (for both Movies and Series) to display library status indicators matching the library view when `inLibrary` is true:
  - Downloaded (`hasFile` or `episodeFileCount > 0`): green `CheckCircle` badge/button and status label.
  - Monitored / Missing (`monitored` and not downloaded): yellow `AlertCircle` badge/button and status label.
  - Unmonitored (`!monitored` and not downloaded): muted `EyeOff` / status indicator and label.
- Open `PreferenceModal` instead of `QuickAddModal` when tapping an existing library item in search results, allowing the user to modify its quality profile, monitoring status, season monitoring, or remove it from Radarr/Sonarr directly from Search.
- Refresh search results after adding a new item via `QuickAddModal` or updating/removing an existing item via `PreferenceModal` so the search row immediately reflects the updated library state.
- Add unit and integration tests covering enriched Radarr/Sonarr search lookup formatting, bridge search dispatch, and search-to-library state transitions.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `telegram-mini-app/client`: Update `Search Media with Visual Results` and `Edit Media Preferences` requirements so search result rows visually distinguish existing library items (downloaded, monitored, unmonitored) and open the preferences modal to edit quality profiles or monitoring directly from search results.
- `media-management/library-mutations`: Update `Query Enriched Library Data` to include enriching search lookup results with library status and configuration fields when a searched movie or series already exists in Radarr or Sonarr.

## Impact

- **Backend (`src/radarr.py`, `src/sonarr.py`)**: `giveTitles()` preserves library status fields from `/api/v3/movie/lookup` and `/api/v3/series/lookup` while keeping `id` as `tmdbId`/`tvdbId` for backward compatibility with the Telegram chat bot (`src/addarr.py`).
- **Frontend (`webapp/src/types.ts`, `webapp/src/components/SearchTab.tsx`)**: `SearchResult` interface extended with optional library fields; `SearchTab` renders library status icons/badges on horizontal search rows and mounts `PreferenceModal` when an existing item is selected.
- **Tests (`tests/test_library_mutations.py`, `tests/test_bridge.py`)**: Unit tests verifying enriched search payloads for both existing and non-existing movies/series in Radarr and Sonarr.
