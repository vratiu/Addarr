# Spec Delta

## Purpose

Provides a responsive Telegram Mini App client interface allowing users to quickly search, browse, add, and manage media in Sonarr and Radarr.

## ADDED Requirements

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
