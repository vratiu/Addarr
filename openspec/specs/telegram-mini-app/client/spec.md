# telegram-mini-app/client Specification

## Purpose
Provides a responsive Telegram Mini App client interface allowing users to quickly search, browse, add, and manage media in Sonarr and Radarr.

## Requirements

### Requirement: Launch Mini App from Telegram
The system SHALL provide entry points within Telegram to launch the Mini App with authenticated user context.

#### Scenario: Open via bot keyboard or menu
- **WHEN** user clicks the Mini App button in the Telegram bot chat
- **THEN** Telegram opens the web application webview with valid `initData` passed in the context

### Requirement: Search Media with Visual Results
The client SHALL allow users to search for movies or series and view results with poster art, year, and overview.

#### Scenario: Search for media title
- **WHEN** user enters a title into the search input
- **THEN** the client displays matching titles with poster art, release year, and overview summary

### Requirement: Single-Screen Quick Add
The client SHALL display a single-screen configuration sheet to add a selected title directly to Sonarr or Radarr.

#### Scenario: Add movie to Radarr
- **WHEN** user taps a movie result and clicks "Add to Radarr" with default or selected quality profile and path
- **THEN** the client dispatches the add command and displays a success confirmation upon completion

### Requirement: Visual Library Browsing
The client SHALL display the existing library of movies and series in a filterable poster grid.

#### Scenario: Filter library by status
- **WHEN** user selects the "Missing" filter in the Movies or Series library view
- **THEN** the client displays only titles that are monitored but not currently downloaded

### Requirement: Edit Media Preferences
The client SHALL allow users to modify quality profiles, monitoring status, and season monitoring for existing library items.

#### Scenario: Change quality profile of an existing title
- **WHEN** user selects a new quality profile for an existing movie or series and confirms
- **THEN** the client submits the update command and reflects the updated profile immediately

### Requirement: Calendar Tab Navigation and Media Type Persistence
The client SHALL provide a "Calendar" tab alongside "Search & Add" and "My Library" that displays upcoming releases for the selected media type and retains the active tab when switching between Movies and Series.

#### Scenario: Switch from Movies to Series while on Calendar tab
- **WHEN** user is viewing the "Calendar" tab with "Movies" selected and clicks the "Series" media type toggle
- **THEN** the client remains on the "Calendar" tab and loads upcoming series episode releases without resetting to "Search & Add"

#### Scenario: Switch from Series to Movies while on Calendar tab
- **WHEN** user is viewing the "Calendar" tab with "Series" selected and clicks the "Movies" media type toggle
- **THEN** the client remains on the "Calendar" tab and loads upcoming digital movie releases

### Requirement: Upcoming Release List and Relative Date Formatting
The client SHALL render upcoming calendar entries in a chronological list (up to 60 days and at most 20 entries) showing the formatted release date and a relative day indicator for releases occurring in fewer than 14 days.

#### Scenario: Display release date less than 14 days away
- **WHEN** a calendar entry has a release date fewer than 14 days from the current date (e.g., 3 days from today)
- **THEN** the client displays both the formatted calendar date and the relative day offset (e.g., `(in 3 days)`, `(tomorrow)`, or `(today)`)

#### Scenario: Display release date 14 or more days away
- **WHEN** a calendar entry has a release date between 14 and 60 days from the current date
- **THEN** the client displays the formatted calendar date without a relative day suffix

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

