# Proposal

## Why

When users open the Telegram Mini App on the Movies search tab (`Search & Add`), they currently see an empty placeholder asking them to type a title. Displaying a poster grid of movie suggestions from Radarr's Explore feed (specifically popular and trending titles, excluding personalized library recommendations) gives users immediate, visual discovery and one-tap adding without blocking initial page startup or overloading Radarr with repeated upstream requests. Additionally, users need a way inside `QuickAddModal` to inspect the movie's full details and ratings via an external IMDb link before adding it to their library.

## What Changes

- Query Radarr's Discover endpoint (`GET /api/v3/importlist/movie`) specifically with `includeTrending=true` and `includePopular=true` while setting `includeRecommendations=false` to return a unique, deduplicated list of trending and popular titles without library-based recommendations, excluding movies already in the library (`isExisting`) or on the exclusion list (`isExcluded`), and capping the result at 24 movies.
- Pass `imdbId` in movie search and discover payloads across `radarr.py` and `bridge.py`, adding `imdbId?: string` to `SearchResult` in `webapp/src/types.ts`.
- In `QuickAddModal.tsx`, display an IMDb link button/badge next to the movie title/year that opens the movie's IMDb page (`https://www.imdb.com/title/${imdbId}/` or a title search fallback) in Telegram WebApp.
- Maintain the 1-hour in-memory cache in `src/radarr.py` (and frontend client cache in `webapp/src/services/bridge.ts`) and automatic cache eviction when a movie is added.
- Ensure Python `< 3.12` compatibility in `src/bridge.py` logging.

## Capabilities

### New Capabilities
- `media-management/movie-discovery`: Fetching, filtering, deduplicating, and caching (1-hour TTL) up to 24 movie suggestions from Radarr's Explore feed (`includeTrending=true`, `includePopular=true`, `includeRecommendations=false`), providing `imdbId` metadata.

### Modified Capabilities
- `telegram-mini-app/client`: Non-blocking loading and rendering of trending and popular suggestions on the Movies search tab, and providing an IMDb button/link in `QuickAddModal` to view full movie details.
- `telegram-mini-app/bridge`: Dispatching `get_discover_movies` over the Firebase RTDB bridge and ensuring Python `< 3.12` compatibility in bridge logging.

## Impact

- **Backend (`src/radarr.py`, `src/bridge.py`)**:
  - `radarr.get_discover_movies` sets `includeRecommendations="false"`, `includeTrending="true"`, `includePopular="true"`, and extracts `imdbId`.
  - `radarr.giveTitles` retains `imdbId` when searching.
- **Frontend (`webapp/src/types.ts`, `webapp/src/components/QuickAddModal.tsx`)**:
  - `SearchResult` includes optional `imdbId: string`.
  - `QuickAddModal` renders an IMDb button/icon link.
- **Tests (`tests/test_bridge.py`)**:
  - Update unit tests to verify `includeRecommendations=false`, `includeTrending=true`, `includePopular=true`, and `imdbId` propagation.
