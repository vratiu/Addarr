# Spec Delta

## Purpose

Provides movie discovery suggestions from Radarr's Explore/Discover feeds (specifically trending and popular titles, excluding library recommendations) with 1-hour caching and IMDb metadata to prevent excessive upstream queries.

## ADDED Requirements

### Requirement: Fetch Discover Movie Suggestions
The system SHALL query Radarr's `importlist/movie` endpoint with `includeTrending=true`, `includePopular=true`, and `includeRecommendations=false`, exclude existing or excluded movies, deduplicate by `tmdbId`, and return up to 24 movie suggestions with IMDb metadata.

#### Scenario: Retrieve trending and popular discover feeds
- **WHEN** movie discovery suggestions are requested and the cache is empty or expired
- **THEN** the system queries Radarr with `includeTrending=true`, `includePopular=true`, and `includeRecommendations=false`, filters out items where `isExisting` or `isExcluded` is true, deduplicates by `tmdbId`, and returns at most 24 items with `id` (`tmdbId`), `title`, `year`, `overview`, `poster`, and `imdbId` (when available)

### Requirement: Cache Discover Suggestions for One Hour
The system SHALL cache the discover movie suggestions for 1 hour (3600 seconds) so Radarr's discover endpoint is queried at most once per hour.

#### Scenario: Subsequent request within one hour
- **WHEN** movie discovery suggestions are requested within 3600 seconds of a successful fetch
- **THEN** the system returns the cached suggestions without making an HTTP request to Radarr's `importlist/movie` endpoint

#### Scenario: Request after cache expiration
- **WHEN** movie discovery suggestions are requested 3600 seconds or more after the previous fetch
- **THEN** the system queries Radarr's `importlist/movie` endpoint for fresh suggestions and updates the cache timestamp

#### Scenario: Evict added movie from cache
- **WHEN** a user successfully adds a movie to Radarr via `addToLibrary`
- **THEN** the system removes that movie's `tmdbId` from the cached discover suggestions list immediately
