# Proposal

## Why

When users open the Telegram Mini App on the Movies search tab (`Search & Add`), they currently see an empty placeholder asking them to type a title. Displaying a poster grid of movie suggestions from Radarr's Discover/Explore feed (`importlist/movie` combining recommendations, trending, and popular titles) gives users immediate, visual discovery and one-tap adding without blocking initial page startup or overloading Radarr with repeated upstream requests. Additionally, a Python `< 3.12` f-string backslash syntax error in `src/bridge.py` (line 209) currently prevents the Mini App bridge task from starting on Python 3.9–3.11 runtimes.

## What Changes

- Fix the Python `< 3.12` `SyntaxError: f-string expression part cannot include a backslash` in `src/bridge.py` (`_resolve_tags`) by extracting the regex substitution prior to formatting the log message.
- Query Radarr's Discover endpoint (`GET /api/v3/importlist/movie` with `includeRecommendations=true`, `includeTrending=true`, and `includePopular=true`) to fetch movie suggestions, excluding titles already in the library (`isExisting`) or on the exclusion list (`isExcluded`), deduplicating by `tmdbId`, and capping the result at 24 movies.
- Add a 1-hour (3600-second) in-memory cache in `src/radarr.py` (and matching client-side cache in `webapp/src/services/bridge.ts`) so Radarr's recommendation/discover endpoint is queried at most once per hour, and automatically evict a movie from the cached suggestions when it is added to the library.
- Expose a `get_discover_movies` action in the Addarr Firebase RTDB bridge (`src/bridge.py`) and frontend `BridgeService` (`webapp/src/services/bridge.ts`).
- Update `SearchTab.tsx` so that when `mediaType === 'movie'` and the search input is empty, the page renders immediately without blocking startup and asynchronously loads and displays the 24-movie Discover suggestions poster grid. Tapping any suggestion opens `QuickAddModal` to add the movie to Radarr and removes it from the grid upon success.

## Capabilities

### New Capabilities
- `media-management/movie-discovery`: Fetching, filtering, deduplicating, and caching (1-hour TTL) up to 24 movie suggestions from Radarr's Discover feed (`includeRecommendations`, `includeTrending`, `includePopular`).

### Modified Capabilities
- `telegram-mini-app/client`: Non-blocking loading and rendering of the Radarr Discover suggestions poster grid on the Movies search tab when the search query is empty, with `QuickAddModal` integration.
- `telegram-mini-app/bridge`: Dispatching `get_discover_movies` over the Firebase RTDB bridge and ensuring Python `< 3.12` compatibility in bridge logging.

## Impact

- **Backend (`src/radarr.py`, `src/bridge.py`)**:
  - New `get_discover_movies(limit=24)` helper and 1-hour in-memory cache (`_discover_cache`) in `src/radarr.py`, plus cache eviction in `addToLibrary`.
  - New `get_discover_movies` action in `src/bridge.py` `dispatch_action` and fix for the f-string backslash syntax error in `_resolve_tags`.
- **Frontend (`webapp/src/services/bridge.ts`, `webapp/src/components/SearchTab.tsx`)**:
  - New `getDiscoverMovies(limit)` method with 1-hour client-side cache and cache eviction on `addMovie` in `webapp/src/services/bridge.ts`.
  - Updated `webapp/src/components/SearchTab.tsx` to asynchronously load and render the poster grid of Discover suggestions when `mediaType === 'movie'` and the search query is empty.
- **Tests (`tests/test_bridge.py`)**:
  - Unit tests covering `radarr.get_discover_movies` filtering/deduplication/1-hour caching, cache eviction on add, `get_discover_movies` bridge dispatch, and Python syntax/import verification.
