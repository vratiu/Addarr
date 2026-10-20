# Tasks

## 1. Backend Search Enrichment (Radarr & Sonarr)

- [x] 1.1 Update `radarr.giveTitles()` in `src/radarr.py` to detect existing library items (`id > 0`), resolve poster URLs with `images` fallback, and include `inLibrary`, `libraryId`, `qualityProfileId`, `monitored`, `status`, `hasFile`, and `sizeOnDisk` while keeping `id` as `tmdbId`; verify with unit tests in `tests/test_library_mutations.py`.
- [x] 1.2 Update `sonarr.giveTitles()` in `src/sonarr.py` to detect existing library items (`id > 0`), resolve poster URLs with `images` fallback, and include `overview`, `inLibrary`, `libraryId`, `qualityProfileId`, `monitored`, `status`, `episodeCount`, `episodeFileCount`, and `seasons` while keeping `id` as `tvdbId`; verify with unit tests in `tests/test_library_mutations.py`.
- [x] 1.3 Add unit tests in `tests/test_library_mutations.py` and `tests/test_bridge.py` covering `radarr.giveTitles()`, `sonarr.giveTitles()`, and `bridge.dispatch_action` (`search_movie`, `search_series`) for both existing library items (`id > 0`) and new lookup items (`id == 0` or omitted), and run `pytest` / `unittest` to confirm all tests pass.

## 2. Mini App Frontend Search Status & Preference Editing

- [x] 2.1 Extend `SearchResult` in `webapp/src/types.ts` with optional library metadata fields (`inLibrary`, `libraryId`, `qualityProfileId`, `monitored`, `status`, `hasFile`, `sizeOnDisk`, `episodeCount`, `episodeFileCount`, `seasons`) and verify TypeScript compilation.
- [x] 2.2 Update `SearchTab.tsx` in `webapp/src/components/SearchTab.tsx` to render library status badges (`Downloaded`, `Monitored`, `Unmonitored`) and corresponding right-side status icons (`CheckCircle`, `AlertCircle`, `EyeOff`) on horizontal search rows when `item.inLibrary` is true, and verify the build succeeds.
- [x] 2.3 Update `SearchTab.tsx` to open `PreferenceModal` when tapping an existing library item (`inLibrary && libraryId`), open `QuickAddModal` when tapping a non-library item, and refresh search results after adding, updating, or deleting an item; verify with `npm run build` in `webapp/`.
