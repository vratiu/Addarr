# Spec Delta

## ADDED Requirements

### Requirement: Display Radarr Discover Suggestions Grid on Movies Search Page
When the user lands on the Movies search tab with an empty search query, the client SHALL asynchronously load and display a poster grid of up to 24 movie suggestions from Radarr's Explore/Discover feed (trending and popular) without blocking initial page startup.

#### Scenario: Non-blocking load of suggestions on Movies search page
- **WHEN** the user opens or switches to the Search tab with `Movies` selected and an empty search input
- **THEN** the search input renders immediately without blocking page startup, and the client asynchronously loads and renders a poster grid of up to 24 Radarr Discover movie suggestions

#### Scenario: Hide suggestions when typing a search query
- **WHEN** the user enters a non-empty search query into the Movies search input
- **THEN** the client hides the suggestions grid and displays matching search results instead

#### Scenario: Quick-add a movie from the suggestions grid
- **WHEN** the user taps a movie card in the suggestions grid and confirms adding it in the quick-add sheet
- **THEN** the client adds the movie to Radarr, displays a confirmation banner, and removes the added movie from the suggestions grid

### Requirement: IMDb Link in Quick Add Modal
The quick add modal SHALL display an IMDb button or link allowing users to view movie details on IMDb.

#### Scenario: View movie details on IMDb
- **WHEN** the user opens the quick-add modal for a movie and taps the IMDb button
- **THEN** the client opens the movie's IMDb page in an external browser view using its `imdbId` or title search fallback
