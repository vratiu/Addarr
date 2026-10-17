# Design

## Context

The Telegram Mini App currently renders `SearchTab.tsx` as its default landing view (`activeTab === 'search'`, `mediaType === 'movie'`). When the search input is empty, it renders static placeholder text. Meanwhile, Radarr exposes its Explore/Discover feed at `GET /api/v3/importlist/movie` (`ImportListMoviesController.GetDiscoverMovies`), which aggregates TMDb recommendations, trending movies, popular movies, and configured import lists. Additionally, `src/bridge.py` line 209 contains an f-string expression with a raw backslash (`{_APIKEY_SCRUB_RE.sub(r'\1***', str(e))}`) which raises a `SyntaxError` on Python `< 3.12`. See `proposal.md` for motivation and `specs/` for behavioral requirements.

## Goals / Non-Goals

**Goals:**
- Ensure `src/bridge.py` imports cleanly on Python 3.9–3.11 as well as 3.12+ by removing backslashes inside f-string expressions.
- Query Radarr's `importlist/movie` endpoint with `includeRecommendations=true`, `includeTrending=true`, and `includePopular=true`, filtering out movies already in the library (`isExisting`) or excluded (`isExcluded`), deduplicating by `tmdbId`, and slicing to 24 items.
- Enforce a 1-hour (3600s) cache TTL so Radarr's discover endpoint is never queried more than once per hour, while immediately evicting newly added movies from the cache.
- Load and render the 24-movie poster grid asynchronously on `SearchTab.tsx` when `mediaType === 'movie'` and the search input is empty, without blocking initial page startup or search input responsiveness.

**Non-Goals:**
- Adding discover suggestions for Sonarr (`mediaType === 'series'`), as the request specifically targets Radarr's Explore page on the Movies search view.
- Persisting the backend discover cache across Addarr process restarts (in-memory caching with a 1-hour TTL is sufficient and avoids disk I/O).

## Decisions

### 1. Two-Layer 1-Hour Cache (Backend In-Memory + Frontend Client Cache)
- **Decision**:
  - **Backend (`src/radarr.py`)**: Maintain a module-level `_discover_cache = {"timestamp": 0.0, "items": []}` with `DISCOVER_CACHE_TTL = 3600`. When `get_discover_movies(limit=24)` is called and `time.time() - _discover_cache["timestamp"] < 3600` (with non-empty items), return `_discover_cache["items"][:limit]` without calling Radarr. When `addToLibrary(tmdbId, ...)` succeeds, remove any item matching `int(tmdbId)` from `_discover_cache["items"]`.
  - **Frontend (`webapp/src/services/bridge.ts`)**: Cache the fetched `SearchResult[]` list in memory and `localStorage` (`addarr_discover_movies_cache_v1`) with a 1-hour (3,600,000 ms) timestamp. On `addMovie(tmdbId, ...)`, remove the added movie `id` from the client cache as well.
- **Rationale**: The backend cache guarantees Radarr's `/api/v3/importlist/movie` (which makes external calls to TMDb/Radarr's metadata proxy) is never hit more than once per hour regardless of how many users open the Mini App or clear their webview cache. The frontend cache makes switching tabs or reopening the Mini App instantaneous without waiting for a Firebase RTDB round-trip.
- **Alternatives considered**:
  - Frontend-only caching: Rejected because multiple users or fresh Telegram webview sessions would still trigger Radarr API calls more than once per hour.
  - Backend-only caching: Kept alongside lightweight frontend caching so tab switches inside the Mini App do not incur unnecessary RTDB traffic.

### 2. Filtering, Poster Extraction, and Normalization in `radarr.get_discover_movies`
- **Decision**: Call `commons.generateApiQuery("radarr", "importlist/movie", {"includeRecommendations": "true", "includeTrending": "true", "includePopular": "true"})`. For each movie in the JSON list:
  - Skip if `movie.get("isExisting")` or `movie.get("isExcluded")` is truthy, or if `tmdbId` is missing or already seen.
  - Extract poster URL by checking `movie.get("images", [])` for `coverType == "poster"` (`remoteUrl` or `url`), falling back to `movie.get("remotePoster")`.
  - Map each movie to the `SearchResult` shape (`{"id": movie["tmdbId"], "title": movie["title"], "year": movie.get("year"), "overview": movie.get("overview", ""), "poster": poster}`) so `SearchTab` and `QuickAddModal` can consume suggestion items identically to search results.
  - Store the full filtered list in `_discover_cache["items"]` (so evicting an added movie still leaves up to 24 items available) and return `items[:int(limit)]`.
- **Rationale**: Mapping directly to `SearchResult` allows tapping a poster in the suggestions grid to open `QuickAddModal` with zero adapter code. Storing the filtered list before slicing to `limit` ensures that if a user adds a movie from the grid, subsequent reads still have a full 24-item grid from the remaining cached items.

### 3. Non-Blocking Startup in `SearchTab.tsx`
- **Decision**: Render the `SearchTab` shell and search input immediately on mount. Trigger `bridge.getDiscoverMovies()` inside a `useEffect` when `mediaType === 'movie'`. Track `suggestionsLoading` separately from `loading` (which is for active search queries) so the search input is never disabled or blocked while suggestions load in the background. When `query.trim()` is empty and `mediaType === 'movie'`, render the 3-to-4 column poster grid (`grid-cols-3 sm:grid-cols-4 gap-3`, matching `LibraryTab`'s poster card layout with a subtle `+` badge and section header).
- **Rationale**: Ensures zero impact on time-to-interactive when launching the Mini App; if a user starts typing immediately, the view seamlessly switches to search results even if the discover fetch is still in flight.

## Risks / Trade-offs

- **[Risk] Radarr `importlist/movie` can be slow on a cold cache (upstream TMDb/SkyHook metadata lookup)** → **Mitigation**: Use a generous timeout (`REQUEST_TIMEOUT = 15`s) in `radarr.py`, load asynchronously in `SearchTab.tsx` without blocking the search input, and fall back gracefully to the standard search prompt if Radarr returns an error or empty list.
- **[Risk] Python `< 3.12` f-string syntax incompatibility** → **Mitigation**: Extract `_APIKEY_SCRUB_RE.sub(...)` into a local variable `safe_msg` before the f-string in `_resolve_tags` (matching the pattern already used in `dispatch_action`).
