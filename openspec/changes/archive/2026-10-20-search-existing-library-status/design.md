# Design

## Context

See `proposal.md` for motivation. Currently, `radarr.giveTitles()` (`src/radarr.py`) and `sonarr.giveTitles()` (`src/sonarr.py`) format responses from `/api/v3/movie/lookup` and `/api/v3/series/lookup` into minimal dictionaries where `id` is set to `tmdbId` or `tvdbId`. Both the legacy Telegram conversational bot (`src/addarr.py`) and the Mini App bridge (`src/bridge.py`) call `giveTitles()`.

When a searched movie or series already exists in Radarr or Sonarr, the upstream `/lookup` endpoint already includes the local database record fields (`id > 0`, `qualityProfileId > 0`, `monitored`, `status`, `hasFile`, `sizeOnDisk`, `statistics`, `seasons`, `images`). However, `giveTitles()` currently drops `id` (overwriting it with `tmdbId`/`tvdbId`) and omits the library configuration fields needed by `PreferenceModal.tsx`.

## Goals / Non-Goals

**Goals:**
- Expose existing library status and configuration metadata in `search_movie` and `search_series` responses without making extra HTTP calls to Radarr/Sonarr.
- Preserve backward compatibility with `src/addarr.py`, which expects `result["id"]` to be `tmdbId` (for movies) or `tvdbId` (for series).
- Render clear library status badges and icons (`CheckCircle`, `AlertCircle`, `EyeOff`) on the horizontal search result rows in `SearchTab.tsx`.
- Open `PreferenceModal` directly from `SearchTab.tsx` when tapping an existing library item, and refresh search results after any add, update, or delete operation.

**Non-Goals:**
- Changing the layout of search results from horizontal list rows to a poster grid.
- Adding existing-library badges to the Radarr Discover suggestions grid (which already filters out `isExisting` items).

## Decisions

### 1. Enrich `giveTitles()` in `radarr.py` and `sonarr.py` with zero extra API calls
- **Decision**: Inspect each lookup item in `radarr.giveTitles()` and `sonarr.giveTitles()`. If `item.get("id")` is an integer `> 0`, set `inLibrary = True` and `libraryId = item["id"]` alongside `id = item["tmdbId"]` (or `tvdbId`). Also extract `qualityProfileId`, `monitored`, `status`, `hasFile`, `sizeOnDisk` (for movies), and `overview`, `episodeCount`, `episodeFileCount`, `seasons` (for series). Also resolve `poster` using the `images` array (`remoteUrl` / `url`) as fallback if `remotePoster` is missing, matching `get_library_summary()`.
- **Alternatives considered**:
  - *Cross-referencing `get_library_summary()` on the client or in `bridge.py`*: Requires a second round-trip to Radarr/Sonarr on every search or preloading the entire library on tab mount. Since `/movie/lookup` and `/series/lookup` natively return the database `id` and library fields for existing items, enriching `giveTitles()` is faster and always up to date.

### 2. Map `SearchResult` to `LibraryItem` in `SearchTab.tsx` for `PreferenceModal`
- **Decision**: Extend `SearchResult` in `webapp/src/types.ts` with optional library fields (`inLibrary?: boolean`, `libraryId?: number`, `qualityProfileId?: number`, `monitored?: boolean`, `status?: string`, `hasFile?: boolean`, `sizeOnDisk?: number`, `episodeCount?: number`, `episodeFileCount?: number`, `seasons?: Array<{ seasonNumber: number; monitored: boolean }>`).
- In `SearchTab.tsx`, when a user clicks a search result where `item.inLibrary && item.libraryId`:
  - Construct a `LibraryItem` object (using `id: item.libraryId`, `tmdbId: mediaType === 'movie' ? item.id : undefined`, `tvdbId: mediaType === 'series' ? item.id : undefined`, etc.) and set `editingLibraryItem` state to open `PreferenceModal`.
  - When `item.inLibrary` is falsy, continue setting `selectedItem` to open `QuickAddModal`.

### 3. Visual Status Indicators on Horizontal Search Rows
- **Decision**: Keep the horizontal row layout in `SearchTab.tsx` and differentiate the right-side action button and metadata line based on library state:
  - **Downloaded** (`inLibrary && (hasFile || (episodeFileCount && episodeFileCount > 0))`):
    - Metadata pill: green `Downloaded` badge
    - Action button: green `CheckCircle` icon button (`bg-green-950/80 border border-green-500/70 text-green-400`)
  - **Monitored / Missing** (`inLibrary && monitored && !downloaded`):
    - Metadata pill: yellow `Monitored` badge
    - Action button: yellow `AlertCircle` icon button (`bg-yellow-950/80 border border-yellow-500/70 text-yellow-400`)
  - **Unmonitored** (`inLibrary && !monitored && !downloaded`):
    - Metadata pill: gray `Unmonitored` badge
    - Action button: muted `EyeOff` icon button (`bg-gray-800/80 border border-gray-600/70 text-gray-400`)
  - **Not in Library** (`!inLibrary`):
    - Action button: existing blue `Plus` (`+`) button (`bg-tg-button/20 text-tg-link`)

### 4. Immediate Post-Action Refresh in Search
- **Decision**: Extract a reusable `runSearch(searchQuery, currentMediaType)` helper in `SearchTab.tsx`. Call it after `QuickAddModal` `onSuccess` (when `query.trim()` is non-empty) and after `PreferenceModal` `onUpdated` so the row immediately updates its icon, quality profile, or monitoring state without requiring the user to re-type their query.

## Risks / Trade-offs

- **[Risk] Legacy Telegram Bot (`src/addarr.py`) relies on `giveTitles()`** → **Mitigation**: Keep `id` mapped to `tmdbId`/`tvdbId` and all existing keys intact; only add new keys (`inLibrary`, `libraryId`, `qualityProfileId`, etc.) which `src/addarr.py` safely ignores.
- **[Risk] Lookup item has `id: 0` or `None` when not in library** → **Mitigation**: Explicitly check `bool(raw_id and int(raw_id) > 0)` before marking `inLibrary: True`.
