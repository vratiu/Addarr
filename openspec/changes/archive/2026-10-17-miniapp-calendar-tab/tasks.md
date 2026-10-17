# Tasks

## 1. Backend Calendar Queries (Radarr & Sonarr)

- [x] 1.1 Implement `get_calendar_movies(days=60, limit=20)` in `src/radarr.py` querying `/api/v3/calendar`, filtering strictly for movies with `digitalRelease` within `[today, today + days]`, sorting ascending by `digitalRelease`, and capping at `limit` entries; verify by inspecting `src/radarr.py`.
- [x] 1.2 Implement `get_calendar_series(days=60, limit=20)` in `src/sonarr.py` querying `/api/v3/calendar` with `includeSeries=true`, grouping multiple episodes of the same series and season airing on the same date into a single entry, sorting ascending by air date, and capping at `limit` entries; verify by inspecting `src/sonarr.py`.
- [x] 1.3 Add unit tests for `radarr.get_calendar_movies` (including digital-only filtering and 20-item cap) and `sonarr.get_calendar_series` (including single episode and same-day multi-episode grouping) in `tests/test_library_mutations.py` and verify they pass with `pytest tests/test_library_mutations.py`.

## 2. Bridge Dispatch & Authorization

- [x] 2.1 Add `get_calendar_movies` and `get_calendar_series` to `_requires_admin` and `dispatch_action` in `src/bridge.py`, and add bridge tests in `tests/test_bridge.py`; verify all bridge tests pass with `pytest tests/test_bridge.py`.

## 3. Mini App Frontend Calendar Tab & Relative Date Formatting

- [x] 3.1 Add `CalendarItem` interface and `TabType` (`'search' | 'library' | 'calendar'`) to `webapp/src/types.ts` and implement `getCalendar(type: MediaType)` in `webapp/src/services/bridge.ts`; verify TypeScript types compile without errors.
- [x] 3.2 Create `webapp/src/components/CalendarTab.tsx` displaying up to 20 upcoming digital movie or series episode entries in a list, calculating relative days (`(today)`, `(tomorrow)`, `(in X days)`) for dates `< 14` days away, and re-fetching when `mediaType` changes; verify component renders both movie and series item layouts.
- [x] 3.3 Update `webapp/src/components/Navbar.tsx` and `webapp/src/App.tsx` to add the "Calendar" tab button and keep `activeTab` preserved when toggling between "Movies" and "Series"; verify the frontend production bundle builds cleanly via `npm run build` in `webapp/`.
