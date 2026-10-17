# Tasks

## 1. Backend Bugfix & Radarr Discover API (`src/bridge.py`, `src/radarr.py`)

- [x] 1.1 Fix the Python `< 3.12` f-string backslash syntax error in `src/bridge.py` (`_resolve_tags`, line 209) by extracting `safe_msg = _APIKEY_SCRUB_RE.sub(r"\1***", str(e))` before formatting the log string, and verify `src/bridge.py` contains no f-string expressions with backslashes via AST/regex check and `pytest`.
- [x] 1.2 Implement `get_discover_movies(limit=24)` and the 1-hour (3600s) in-memory cache (`_discover_cache`) in `src/radarr.py` querying `importlist/movie` with `includeRecommendations=true`, `includeTrending=true`, and `includePopular=true`, filtering out `isExisting` and `isExcluded` movies, deduplicating by `tmdbId`, and evicting added `tmdbId`s in `addToLibrary`, then verify with unit tests in `tests/test_bridge.py`.
- [x] 1.3 Add `get_discover_movies` action handling in `src/bridge.py` (`dispatch_action`) and verify with unit tests in `tests/test_bridge.py` covering dispatch, custom limit, and 1-hour caching behavior.

## 2. Mini App Frontend Suggestions Grid (`webapp/src/`)

- [x] 2.1 Add `getDiscoverMovies(limit = 24)` with 1-hour client-side caching (`addarr_discover_movies_cache_v1`) and cache eviction inside `addMovie` in `webapp/src/services/bridge.ts`, and verify TypeScript compilation succeeds (`npm run build` in `webapp/`).
- [x] 2.2 Update `webapp/src/components/SearchTab.tsx` to asynchronously load and render the 24-movie Radarr Discover suggestions poster grid when `mediaType === 'movie'` and the search query is empty without blocking initial page startup, allow tapping a suggestion card to open `QuickAddModal`, and remove the movie from the grid upon add, then verify `npm run build` succeeds in `webapp/`.
