# media-management/release-calendar Specification

## Purpose
Provides upcoming release calendar queries for monitored movies (filtered to Digital format releases) in Radarr and monitored series episodes in Sonarr over a 60-day lookahead window, capped at 20 entries and grouped when multiple episodes of a series air on the same date.

## Requirements

### Requirement: Query Upcoming Movie Digital Releases
The system SHALL retrieve monitored movies from Radarr whose `digitalRelease` date falls within the next 60 days from the current date, sorted chronologically ascending and limited to at most 20 entries.

#### Scenario: Include movie with upcoming digital release within 60 days
- **WHEN** the movie calendar query is executed and Radarr returns a monitored movie with a `digitalRelease` date between today and 60 days from today
- **THEN** the system includes the movie in the returned calendar list with its ID, TMDB ID, title, year, poster URL, `digitalRelease` date, monitored status, and download status

#### Scenario: Exclude movie that only has theatrical or physical release in window
- **WHEN** Radarr returns a calendar movie whose `inCinemas` or `physicalRelease` date is within the next 60 days, but its `digitalRelease` date is missing or outside the 60-day window
- **THEN** the system excludes that movie from the returned calendar list

#### Scenario: Cap movie calendar entries at 20 sorted chronologically
- **WHEN** more than 20 monitored movies have `digitalRelease` dates within the 60-day window
- **THEN** the system sorts all matching movies by `digitalRelease` ascending and returns only the earliest 20 entries

### Requirement: Query Upcoming Series Episodes
The system SHALL retrieve monitored episodes from Sonarr airing within the next 60 days from the current date, sorted chronologically ascending and limited to at most 20 entries.

#### Scenario: Retrieve upcoming series episode within 60 days
- **WHEN** the series calendar query is executed and Sonarr returns a single episode of a series airing on a date within the next 60 days
- **THEN** the system returns the entry with series title, poster URL, season number, episode number, episode title, air date, and download status

### Requirement: Group Same-Day Series Episodes
The system SHALL group multiple episodes of the same series and season that air on the same calendar date into a single calendar entry before applying the 20-entry limit.

#### Scenario: Full season or multi-episode drop on the same day
- **WHEN** Sonarr returns multiple monitored episodes for the same series and season airing on the same calendar date (e.g., episodes 1 through 8 of Season 2)
- **THEN** the system collapses those episodes into a single calendar entry indicating the episode range and count (e.g., `S02E01-E08` and episode count `8`) sorted by that air date
