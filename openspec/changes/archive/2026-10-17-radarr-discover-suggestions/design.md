# Design

## Context

The Telegram Mini App currently renders `SearchTab.tsx` as its default landing view (`activeTab === 'search'`, `mediaType === 'movie'`). When the search input is empty, it renders static placeholder text. Meanwhile, Radarr exposes its Explore/Discover feed at `GET /api/v3/importlist/movie` (`ImportListMoviesController.GetDiscoverMovies`), which accepts boolean flags `includeTrending`, `includePopular`, and `includeRecommendations`. The user specifically requested a unique list of trending and popular movies *without* recommendations, as well as an IMDb link in `QuickAddModal.tsx` to view movie details on IMDb. See `proposal.md` for motivation and `specs/` for behavioral requirements.

## Goals / Non-Goals

**Goals:**
- Query Radarr's `importlist/movie` endpoint with `includeTrending=true`, `includePopular=true`, and `includeRecommendations=false`, filtering out movies already in the library (`isExisting`) or excluded (`isExcluded`), deduplicating by `tmdbId`, and slicing to 24 items.
- Propagate `imdbId` (when available) in search and discover payloads across `radarr.py`, `bridge.py`, and `types.ts`.
- Add an IMDb button/link in `QuickAddModal.tsx` opening `https://www.imdb.com/title/${imdbId}/` (or a title search query fallback if `imdbId` is absent) via `window.Telegram?.WebApp?.openLink` or `<a target="_blank">`.
- Enforce the 1-hour (3600s) cache TTL on both backend and frontend so Radarr is queried at most once per hour, while evicting newly added movies from the cache.

**Non-Goals:**
- Adding discover suggestions for Sonarr (`mediaType === 'series'`).
- Displaying IMDb ratings inline (this design opens the IMDb page on demand).

## Decisions

### 1. Feed Configuration in `radarr.py`
- **Decision**: Query `commons.generateApiQuery("radarr", "importlist/movie", {"includeRecommendations": "false", "includeTrending": "true", "includePopular": "true"})`.
- **Rationale**: Omitting recommendations avoids calculating personalized recommendations against existing library items, yielding a cleaner and faster list of globally trending and popular movies.

### 2. IMDb Propagation and Button UI
- **Decision**:
  - In `radarr.py` (`get_discover_movies` and `giveTitles`): include `imdbId: movie.get("imdbId")`.
  - In `webapp/src/types.ts`: add `imdbId?: string` to `SearchResult`.
  - In `webapp/src/components/QuickAddModal.tsx`: Render a styled IMDb button/badge (yellow pill with IMDb logo/text and external link icon) in the header or beside the year/title. When tapped, if `window.Telegram?.WebApp?.openLink` is available, call it; otherwise open in a new tab via `window.open(url, '_blank')`.
  - URL format: If `item.imdbId` is provided, use `https://www.imdb.com/title/${item.imdbId}/`. If not, use `https://www.imdb.com/find/?q=${encodeURIComponent(item.title + ' ' + (item.year || ''))}`.
- **Rationale**: Seamlessly integrates into Telegram WebApp's browser overlay while remaining responsive on desktop browsers.

## Risks / Trade-offs

- **[Risk] Some discover items may not have `imdbId` populated by Radarr's proxy** → **Mitigation**: Provide an automatic fallback link searching IMDb by title and year.
