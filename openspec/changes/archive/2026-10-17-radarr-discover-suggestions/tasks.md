# Tasks

## 1. Backend Adjustments (`src/radarr.py`)

- [x] 1.1 Update `get_discover_movies` in `src/radarr.py` to set `includeRecommendations="false"`, `includeTrending="true"`, `includePopular="true"`, and include `imdbId: movie.get("imdbId")` in returned movie items. Also include `imdbId` in `giveTitles`.
- [x] 1.2 Update unit tests in `tests/test_bridge.py` to verify `includeRecommendations=false` and that `imdbId` is propagated, running tests via `./.venv/bin/python3 -m unittest discover tests/`.

## 2. Frontend IMDb Integration (`webapp/src/`)

- [x] 2.1 Update `SearchResult` in `webapp/src/types.ts` to include `imdbId?: string`.
- [x] 2.2 Add an IMDb button/link in `webapp/src/components/QuickAddModal.tsx` that opens the movie's IMDb page (or fallback search) in an external view, and verify `npm run build` succeeds in `webapp/`.
